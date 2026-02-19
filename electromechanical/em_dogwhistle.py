#!/usr/bin/env python3
"""
Electromechanical UAP Dog Whistle Controller
Drives two simultaneous channels from a Raspberry Pi 5:
  1. RF transmission via HackRF One (optional)
  2. Mechanical transduction via I2S DAC + bass shaker

Usage:
  python3 em_dogwhistle.py                    # Mechanical only (no HackRF needed)
  python3 em_dogwhistle.py --rf               # Both channels
  python3 em_dogwhistle.py --rf --freq 433e6  # Custom RF carrier
  python3 em_dogwhistle.py --duration 1800    # 30 minutes
  python3 em_dogwhistle.py --programme scan   # Frequency scanning mode
"""

import numpy as np
from scipy.io import wavfile
import argparse
import subprocess
import threading
import time
import os
import sys
import signal

SAMPLE_RATE = 44100
RF_SAMPLE_RATE = 2000000  # 2 MHz for HackRF


class MechanicalChannel:
    """Generates low-frequency waveforms for bass shaker ground coupling."""

    def __init__(self, sample_rate=SAMPLE_RATE):
        self.sr = sample_rate

    def schumann_fundamental(self, duration):
        """7.83 Hz — Earth's fundamental Schumann resonance."""
        t = np.linspace(0, duration, int(self.sr * duration), endpoint=False)
        return np.sin(2 * np.pi * 7.83 * t)

    def schumann_second(self, duration):
        """14.3 Hz — Second Schumann harmonic."""
        t = np.linspace(0, duration, int(self.sr * duration), endpoint=False)
        return np.sin(2 * np.pi * 14.3 * t)

    def schumann_combined(self, duration):
        """7.83 Hz + 14.3 Hz combined."""
        return 0.7 * self.schumann_fundamental(duration) + 0.3 * self.schumann_second(duration)

    def infrasound_chirp(self, duration, f_start=1.0, f_end=20.0):
        """Sweep from f_start to f_end Hz."""
        t = np.linspace(0, duration, int(self.sr * duration), endpoint=False)
        freq = f_start + (f_end - f_start) * (t / duration)
        phase = 2 * np.pi * np.cumsum(freq) / self.sr
        return np.sin(phase)

    def breathing_pattern(self, duration, base_freq=7.83, breath_rate=0.25):
        """Base frequency with breathing amplitude modulation."""
        t = np.linspace(0, duration, int(self.sr * duration), endpoint=False)
        carrier = np.sin(2 * np.pi * base_freq * t)
        breath = 0.5 * (1 + np.sin(2 * np.pi * breath_rate * t)) ** 2
        return carrier * breath

    def generate_programme(self, programme, duration):
        """Generate a full programme WAV file."""
        if programme == "schumann":
            signal_data = self.schumann_fundamental(duration)
        elif programme == "combined":
            signal_data = self.schumann_combined(duration)
        elif programme == "chirp":
            signal_data = self.infrasound_chirp(duration)
        elif programme == "breathing":
            signal_data = self.breathing_pattern(duration)
        elif programme == "scan":
            signal_data = self._scan_programme(duration)
        elif programme == "full":
            signal_data = self._full_programme(duration)
        else:
            signal_data = self.schumann_fundamental(duration)

        # Normalise
        max_val = np.max(np.abs(signal_data))
        if max_val > 0:
            signal_data = signal_data / max_val * 0.9

        return np.int16(signal_data * 32767)

    def _scan_programme(self, duration):
        """Scan through Schumann harmonics: 7.83, 14.3, 20.8, 27.3, 33.8 Hz."""
        freqs = [7.83, 14.3, 20.8, 27.3, 33.8]
        segment_dur = duration / len(freqs)
        segments = []
        t = np.linspace(0, segment_dur, int(self.sr * segment_dur), endpoint=False)
        for freq in freqs:
            segments.append(np.sin(2 * np.pi * freq * t))
        return np.concatenate(segments)

    def _full_programme(self, duration):
        """Full cycle matching the combined signal spec."""
        cycle_duration = min(duration, 600)  # 10 min cycle
        repeats = int(np.ceil(duration / cycle_duration))
        segments = []

        # Phase 1: 0:00–0:30 — Schumann fundamental
        segments.append(self.schumann_fundamental(30))
        # Phase 2: 0:30–1:00 — Second harmonic
        segments.append(self.schumann_second(30))
        # Phase 3: 1:00–2:00 — Combined
        segments.append(self.schumann_combined(60))
        # Phase 4: 2:00–3:00 — Chirp sweep
        segments.append(self.infrasound_chirp(60))
        # Phase 5: 3:00–5:00 — Breathing pattern
        segments.append(self.breathing_pattern(120))
        # Phase 6: 5:00–10:00 — Extended combined
        segments.append(self.schumann_combined(300))

        cycle = np.concatenate(segments)
        full = np.tile(cycle, repeats)
        return full[:int(self.sr * duration)]


class RFChannel:
    """Controls HackRF One for RF transmission."""

    def __init__(self, carrier_freq=433e6, sample_rate=RF_SAMPLE_RATE):
        self.carrier_freq = carrier_freq
        self.sr = sample_rate
        self.process = None

    def check_hackrf(self):
        """Check if HackRF is connected."""
        try:
            result = subprocess.run(["hackrf_info"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def generate_baseband(self, duration, mod_freq=7.83, mod_type="am"):
        """Generate baseband IQ samples with modulation."""
        n_samples = int(self.sr * duration)
        t = np.linspace(0, duration, n_samples, endpoint=False)

        if mod_type == "am":
            # AM modulation: carrier modulated by low frequency
            modulator = 0.5 * (1 + np.sin(2 * np.pi * mod_freq * t))
            i = modulator * np.ones(n_samples)
            q = np.zeros(n_samples)
        elif mod_type == "pulse":
            # Pulsed: 1s on, 1s off
            envelope = np.where(t % 2 < 1, 1.0, 0.0)
            i = envelope
            q = np.zeros(n_samples)
        elif mod_type == "cw":
            # Continuous wave
            i = np.ones(n_samples)
            q = np.zeros(n_samples)
        else:
            i = np.ones(n_samples)
            q = np.zeros(n_samples)

        # Interleave I/Q as int8
        iq = np.empty(n_samples * 2, dtype=np.int8)
        iq[0::2] = np.int8(i * 127)
        iq[1::2] = np.int8(q * 127)
        return iq

    def transmit(self, iq_file, duration):
        """Start HackRF transmission."""
        cmd = [
            "hackrf_transfer",
            "-t", iq_file,
            "-f", str(int(self.carrier_freq)),
            "-s", str(self.sr),
            "-x", "20",  # TX gain (dB) — keep low for ISM compliance
            "-R",         # Repeat
        ]
        print(f"  RF TX: {self.carrier_freq/1e6:.1f} MHz, gain 20 dB")
        self.process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return self.process

    def stop(self):
        """Stop transmission."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            self.process = None


class ElectromechanicalController:
    """Synchronised dual-channel controller."""

    def __init__(self, args):
        self.args = args
        self.mech = MechanicalChannel()
        self.rf = RFChannel(carrier_freq=args.freq) if args.rf else None
        self.running = True
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        print("\nShutting down...")
        self.running = False
        if self.rf:
            self.rf.stop()

    def run(self):
        duration = self.args.duration
        programme = self.args.programme

        print("=" * 60)
        print("  ELECTROMECHANICAL UAP DOG WHISTLE")
        print("=" * 60)
        print(f"  Duration:    {duration}s ({duration/60:.0f} min)")
        print(f"  Programme:   {programme}")
        print(f"  Mechanical:  YES (bass shaker / ground coupling)")
        print(f"  RF:          {'YES' if self.rf else 'NO (use --rf to enable)'}")
        if self.rf:
            print(f"  RF Carrier:  {self.args.freq/1e6:.1f} MHz")
        print("=" * 60)

        # Generate mechanical channel
        print("\nGenerating mechanical channel...")
        mech_data = self.mech.generate_programme(programme, duration)
        mech_file = "/tmp/em_mech_output.wav"
        wavfile.write(mech_file, SAMPLE_RATE, mech_data)
        print(f"  Written: {mech_file} ({os.path.getsize(mech_file)/1024/1024:.1f} MB)")

        # Generate RF channel
        rf_file = None
        if self.rf:
            if not self.rf.check_hackrf():
                print("\n⚠️  HackRF not detected! Running mechanical channel only.")
                print("    Connect HackRF One and install hackrf tools.")
                self.rf = None
            else:
                print("\nGenerating RF baseband...")
                # Use shorter RF file that repeats
                rf_segment = min(duration, 60)
                iq_data = self.rf.generate_baseband(rf_segment, mod_freq=7.83, mod_type="am")
                rf_file = "/tmp/em_rf_baseband.iq"
                iq_data.tofile(rf_file)
                print(f"  Written: {rf_file} ({os.path.getsize(rf_file)/1024/1024:.1f} MB)")

        # Start both channels
        print("\n▶ Starting transmission...")
        print("  Press Ctrl+C to stop.\n")

        threads = []

        # Mechanical thread
        def play_mechanical():
            while self.running:
                try:
                    subprocess.run(["aplay", mech_file], timeout=duration + 10)
                except subprocess.TimeoutExpired:
                    pass
                except Exception as e:
                    print(f"  Mechanical error: {e}")
                    break

        t_mech = threading.Thread(target=play_mechanical, daemon=True)
        t_mech.start()
        threads.append(t_mech)
        print("  ✓ Mechanical channel active (ground coupling)")

        # RF thread
        if self.rf and rf_file:
            self.rf.transmit(rf_file, duration)
            print(f"  ✓ RF channel active ({self.args.freq/1e6:.1f} MHz)")

        print(f"\n  Both channels synchronised at {time.strftime('%H:%M:%S')}")
        print(f"  Will run for {duration/60:.0f} minutes.\n")

        # Wait
        start = time.monotonic()
        try:
            while self.running and (time.monotonic() - start) < duration:
                elapsed = time.monotonic() - start
                remaining = duration - elapsed
                mins, secs = divmod(int(remaining), 60)
                print(f"\r  ⏱ {mins:02d}:{secs:02d} remaining", end="", flush=True)
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        # Cleanup
        print("\n\n■ Stopping...")
        self.running = False
        if self.rf:
            self.rf.stop()
            print("  ✓ RF stopped")
        print("  ✓ Mechanical stopped")
        print("  Done.")


def main():
    parser = argparse.ArgumentParser(description="Electromechanical UAP Dog Whistle")
    parser.add_argument("--rf", action="store_true", help="Enable RF channel (requires HackRF One)")
    parser.add_argument("--freq", type=float, default=433e6, help="RF carrier frequency in Hz (default: 433 MHz ISM)")
    parser.add_argument("--duration", type=int, default=3600, help="Duration in seconds (default: 3600)")
    parser.add_argument("--programme", type=str, default="full",
                       choices=["schumann", "combined", "chirp", "breathing", "scan", "full"],
                       help="Signal programme (default: full)")
    parser.add_argument("--mech-only", action="store_true", help="Mechanical channel only (default if no --rf)")
    args = parser.parse_args()

    controller = ElectromechanicalController(args)
    controller.run()


if __name__ == "__main__":
    main()

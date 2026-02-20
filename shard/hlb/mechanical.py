"""
Mechanical Channel — Ground-coupled seismic transduction.
Generates low-frequency WAV files for playback through DAC → amplifier → bass shaker.
"""

import numpy as np
from scipy.io import wavfile
from .constants import AUDIO_SAMPLE_RATE, SCHUMANN_FREQUENCIES
from .waveforms import (
    schumann_envelope, prime_pulse_gate, chirp,
    breathing_envelope, sine, normalise, to_int16
)


class MechanicalChannel:
    """
    Ground-coupled seismic transduction channel.
    
    Generates waveforms at Schumann resonance frequencies for playback
    through a bass shaker bolted to a ground plate.
    
    Signal path: Pi I2S → DAC → Amplifier → Bass Shaker → Ground Plate → Earth
    """
    
    def __init__(self, sample_rate=AUDIO_SAMPLE_RATE):
        self.sr = sample_rate
    
    def schumann_fundamental(self, duration):
        """7.83 Hz — Earth's fundamental resonance."""
        return sine(7.83, duration, self.sr)
    
    def schumann_second(self, duration):
        """14.3 Hz — Second Schumann harmonic."""
        return sine(14.3, duration, self.sr)
    
    def schumann_combined(self, duration):
        """All five Schumann modes, weighted by amplitude."""
        signal = np.zeros(int(self.sr * duration))
        weights = [1.0, 0.7, 0.5, 0.3, 0.2]
        for freq, weight in zip(SCHUMANN_FREQUENCIES, weights):
            signal += weight * sine(freq, duration, self.sr)
        return normalise(signal)
    
    def infrasound_chirp(self, duration, f_start=1.0, f_end=20.0):
        """Sweep through infrasound range."""
        return chirp(f_start, f_end, duration, self.sr)
    
    def schumann_scan(self, duration):
        """Step through each Schumann mode sequentially."""
        segment_dur = duration / len(SCHUMANN_FREQUENCIES)
        segments = [sine(f, segment_dur, self.sr) for f in SCHUMANN_FREQUENCIES]
        return normalise(np.concatenate(segments))
    
    def breathing_schumann(self, duration):
        """Schumann fundamental with breathing amplitude envelope."""
        carrier = sine(7.83, duration, self.sr)
        envelope = breathing_envelope(duration, breath_rate=0.25, sr=self.sr)
        return carrier * envelope
    
    def pulsed_schumann(self, duration):
        """Schumann combined with prime-number pulse gating."""
        signal = self.schumann_combined(duration)
        gate = prime_pulse_gate(duration, self.sr)
        return signal * gate
    
    def generate(self, programme="full", duration=3600):
        """
        Generate a programme.
        
        Programmes:
            fundamental — 7.83 Hz only
            combined    — all 5 Schumann modes
            scan        — step through modes sequentially
            chirp       — sweep 1-20 Hz
            breathing   — 7.83 Hz with breathing envelope
            pulsed      — combined with prime pulse gating
            full        — complete protocol cycle (recommended)
        """
        generators = {
            'fundamental': self.schumann_fundamental,
            'combined': self.schumann_combined,
            'scan': self.schumann_scan,
            'chirp': self.infrasound_chirp,
            'breathing': self.breathing_schumann,
            'pulsed': self.pulsed_schumann,
            'full': self._full_programme,
        }
        
        gen = generators.get(programme, self.schumann_fundamental)
        return normalise(gen(duration))
    
    def _full_programme(self, duration):
        """
        Full protocol cycle (10 min, repeating):
          0:00–0:30  Schumann fundamental
          0:30–1:00  Second harmonic
          1:00–2:00  Combined (all modes)
          2:00–3:00  Infrasound chirp sweep
          3:00–5:00  Breathing Schumann
          5:00–8:00  Pulsed combined (prime timing)
          8:00–10:00 Combined (all modes, sustained)
        """
        segments = [
            self.schumann_fundamental(30),
            self.schumann_second(30),
            self.schumann_combined(60),
            self.infrasound_chirp(60),
            self.breathing_schumann(120),
            self.pulsed_schumann(180),
            self.schumann_combined(120),
        ]
        cycle = np.concatenate(segments)
        cycle_dur = len(cycle) / self.sr
        repeats = int(np.ceil(duration / cycle_dur))
        full = np.tile(cycle, repeats)
        return full[:int(self.sr * duration)]
    
    def save_wav(self, filename, programme="full", duration=3600):
        """Generate and save as WAV file."""
        signal = self.generate(programme, duration)
        wavfile.write(filename, self.sr, to_int16(signal))
        return filename

"""
RF Channel — Hydrogen line transmission via HackRF One.
Generates IQ baseband samples and controls HackRF for transmission.
"""

import numpy as np
import subprocess
import os
import tempfile
from .constants import (
    HYDROGEN_LINE_HZ, RF_SAMPLE_RATE, RF_DEFAULT_GAIN,
    SCHUMANN_FREQUENCIES, ISM_BANDS
)
from .waveforms import schumann_envelope, prime_pulse_gate, normalise, to_iq_int8


class RFChannel:
    """
    RF transmission channel via HackRF One.
    
    Generates IQ baseband samples with Schumann AM modulation
    and prime-number pulse timing, then transmits via hackrf_transfer.
    
    Signal path: Pi USB → HackRF One → RF Amplifier (opt) → Antenna → EM radiation
    """
    
    def __init__(self, carrier_freq=HYDROGEN_LINE_HZ, sample_rate=RF_SAMPLE_RATE,
                 tx_gain=RF_DEFAULT_GAIN):
        self.carrier_freq = carrier_freq
        self.sr = sample_rate
        self.tx_gain = tx_gain
        self.process = None
    
    @staticmethod
    def is_available():
        """Check if HackRF tools are installed and a device is connected."""
        try:
            result = subprocess.run(
                ["hackrf_info"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def generate_baseband(self, duration, modulation="schumann", pulsed=True):
        """
        Generate IQ baseband samples.
        
        Modulations:
            schumann — AM with full Schumann resonance series
            cw       — continuous wave (no modulation)
            single   — AM with fundamental Schumann only (7.83 Hz)
        """
        n_samples = int(self.sr * duration)
        
        if modulation == "schumann":
            envelope = schumann_envelope(duration, sr=self.sr)
        elif modulation == "single":
            envelope = schumann_envelope(
                duration, mode_weights={1: 1.0}, sr=self.sr
            )
        elif modulation == "cw":
            envelope = np.ones(n_samples)
        else:
            envelope = schumann_envelope(duration, sr=self.sr)
        
        # Apply prime pulse gating
        if pulsed:
            gate = prime_pulse_gate(duration, self.sr)
            envelope = envelope * gate
        
        # IQ: envelope modulates I channel, Q stays zero
        # (real-valued AM — HackRF handles upconversion to carrier)
        i_signal = envelope
        q_signal = np.zeros_like(envelope)
        
        return to_iq_int8(i_signal, q_signal)
    
    def save_baseband(self, filename, duration=60, **kwargs):
        """Generate and save IQ baseband to file."""
        iq = self.generate_baseband(duration, **kwargs)
        iq.tofile(filename)
        return filename
    
    def transmit(self, iq_file, repeat=True):
        """
        Start HackRF transmission.
        
        Args:
            iq_file: path to IQ int8 file
            repeat: loop the file continuously
        
        Returns:
            subprocess.Popen process
        """
        cmd = [
            "hackrf_transfer",
            "-t", iq_file,
            "-f", str(int(self.carrier_freq)),
            "-s", str(self.sr),
            "-x", str(self.tx_gain),
        ]
        if repeat:
            cmd.append("-R")
        
        self.process = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
        )
        return self.process
    
    def stop(self):
        """Stop transmission."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
    
    def is_transmitting(self):
        """Check if currently transmitting."""
        return self.process is not None and self.process.poll() is None
    
    @staticmethod
    def legal_frequencies():
        """Return dict of licence-free ISM frequencies for the UK/EU."""
        return ISM_BANDS
    
    def set_frequency(self, freq):
        """Change carrier frequency (requires restart of transmission)."""
        was_tx = self.is_transmitting()
        if was_tx:
            self.stop()
        self.carrier_freq = freq
        # Caller must restart transmission with new frequency
    
    def __del__(self):
        self.stop()

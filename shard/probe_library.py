"""
Probe Library — Structured signal probes for active RF anomaly detection.

Provides a library of probe types designed to elicit potential adaptive
responses from unknown RF phenomena. Each probe is optimized for different
hypothesized response mechanisms.
"""

from enum import Enum
from dataclasses import dataclass
import numpy as np
from typing import Optional, Callable
import sys
import os

# Add hydrogen-line-beacon to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../hydrogen-line-beacon'))
from hlb.constants import (
    HYDROGEN_LINE_HZ,
    SCHUMANN_FREQUENCIES,
    PRIMES,
    RF_SAMPLE_RATE,
)
from hlb.waveforms import (
    sine,
    am_modulate,
    schumann_envelope,
    prime_pulse_gate,
    chirp,
    normalise,
    to_iq_int8,
)


class ProbeType(Enum):
    """Types of probe signals."""
    HYDROGEN_PULSE = "hydrogen_pulse"
    SCHUMANN_AM = "schumann_am"
    FREQUENCY_SWEEP = "frequency_sweep"
    PRIME_SEQUENCE = "prime_sequence"
    FIBONACCI_SEQUENCE = "fibonacci_sequence"
    GOLDEN_RATIO = "golden_ratio"
    CHIRP_UP = "chirp_up"
    CHIRP_DOWN = "chirp_down"
    SILENCE = "silence"
    CUSTOM = "custom"


@dataclass
class Probe:
    """A probe signal configuration.
    
    Attributes
    ----------
    type : ProbeType
        Type of probe.
    parameters : dict
        Probe-specific parameters.
    description : str
        Human-readable description.
    kl_score : float
        Expected KL divergence (for APD policy selection).
    """
    type: ProbeType
    parameters: dict
    description: str
    kl_score: float = 1.0
    
    def __repr__(self):
        return f"Probe({self.type.value}, kl={self.kl_score:.3f})"


class ProbeLibrary:
    """Library of structured probe signals for active discovery.
    
    Generates IQ baseband samples for various probe types, optimized
    for transmission via HackRF One on the hydrogen line or ISM bands.
    
    Parameters
    ----------
    sample_rate : int
        Baseband sample rate in Hz.
    seed : int or None
        Random seed for reproducible probe generation.
    """
    
    def __init__(self, sample_rate: int = RF_SAMPLE_RATE, seed: Optional[int] = None):
        self.sr = sample_rate
        self.rng = np.random.default_rng(seed)
        self._probe_generators = {
            ProbeType.HYDROGEN_PULSE: self._hydrogen_pulse,
            ProbeType.SCHUMANN_AM: self._schumann_am,
            ProbeType.FREQUENCY_SWEEP: self._frequency_sweep,
            ProbeType.PRIME_SEQUENCE: self._prime_sequence,
            ProbeType.FIBONACCI_SEQUENCE: self._fibonacci_sequence,
            ProbeType.GOLDEN_RATIO: self._golden_ratio,
            ProbeType.CHIRP_UP: self._chirp_up,
            ProbeType.CHIRP_DOWN: self._chirp_down,
            ProbeType.SILENCE: self._silence,
        }
    
    def get_standard_library(self) -> list[Probe]:
        """Return the standard probe library with KL scores.
        
        KL scores are assigned based on signal power and information content.
        Higher scores indicate stronger expected discrimination between H0/H1.
        """
        return [
            Probe(
                type=ProbeType.HYDROGEN_PULSE,
                parameters={"pulsed": True, "duty_cycle": 0.5},
                description="Pulsed carrier on hydrogen line (1420.405 MHz)",
                kl_score=2.5,
            ),
            Probe(
                type=ProbeType.SCHUMANN_AM,
                parameters={"mode_weights": {1: 1.0, 2: 0.7, 3: 0.5}},
                description="AM modulated by Schumann resonances (7.83 Hz fundamental)",
                kl_score=3.0,
            ),
            Probe(
                type=ProbeType.FREQUENCY_SWEEP,
                parameters={"f_start": 1000, "f_end": 10000, "sweep_type": "linear"},
                description="Linear frequency sweep 1-10 kHz baseband",
                kl_score=2.0,
            ),
            Probe(
                type=ProbeType.PRIME_SEQUENCE,
                parameters={"primes": PRIMES[:10]},
                description="Prime number pulse intervals (2, 3, 5, 7...)",
                kl_score=2.8,
            ),
            Probe(
                type=ProbeType.FIBONACCI_SEQUENCE,
                parameters={"length": 10},
                description="Fibonacci sequence pulse intervals",
                kl_score=2.6,
            ),
            Probe(
                type=ProbeType.GOLDEN_RATIO,
                parameters={"phi_periods": 5},
                description="Golden ratio (φ) modulated carrier",
                kl_score=2.4,
            ),
            Probe(
                type=ProbeType.CHIRP_UP,
                parameters={"f_start": 500, "f_end": 5000},
                description="Upward chirp 500 Hz → 5 kHz",
                kl_score=1.8,
            ),
            Probe(
                type=ProbeType.CHIRP_DOWN,
                parameters={"f_start": 5000, "f_end": 500},
                description="Downward chirp 5 kHz → 500 Hz",
                kl_score=1.8,
            ),
            Probe(
                type=ProbeType.SILENCE,
                parameters={},
                description="Silent probe (control/baseline)",
                kl_score=0.1,
            ),
        ]
    
    def generate_iq(self, probe: Probe, duration: float) -> np.ndarray:
        """Generate IQ baseband samples for a probe.
        
        Parameters
        ----------
        probe : Probe
            Probe configuration.
        duration : float
            Duration in seconds.
        
        Returns
        -------
        np.ndarray
            Interleaved IQ int8 samples for HackRF.
        """
        generator = self._probe_generators.get(probe.type)
        if generator is None:
            raise ValueError(f"Unknown probe type: {probe.type}")
        
        return generator(duration, probe.parameters)
    
    # ==================== Probe Generators ====================
    
    def _hydrogen_pulse(self, duration: float, params: dict) -> np.ndarray:
        """Pulsed hydrogen line carrier."""
        n_samples = int(self.sr * duration)
        pulsed = params.get("pulsed", True)
        duty_cycle = params.get("duty_cycle", 0.5)
        
        if pulsed:
            gate = prime_pulse_gate(duration, self.sr)
        else:
            gate = np.ones(n_samples)
        
        i_signal = gate
        q_signal = np.zeros_like(gate)
        return to_iq_int8(i_signal, q_signal)
    
    def _schumann_am(self, duration: float, params: dict) -> np.ndarray:
        """Schumann resonance AM modulation."""
        mode_weights = params.get("mode_weights", {1: 1.0, 2: 0.7, 3: 0.5, 4: 0.3, 5: 0.2})
        envelope = schumann_envelope(duration, mode_weights, sr=self.sr)
        
        i_signal = envelope
        q_signal = np.zeros_like(envelope)
        return to_iq_int8(i_signal, q_signal)
    
    def _frequency_sweep(self, duration: float, params: dict) -> np.ndarray:
        """Frequency sweep (chirp) probe."""
        f_start = params.get("f_start", 1000)
        f_end = params.get("f_end", 10000)
        
        sweep = chirp(f_start, f_end, duration, self.sr)
        i_signal = sweep
        q_signal = np.zeros_like(sweep)
        return to_iq_int8(i_signal, q_signal)
    
    def _prime_sequence(self, duration: float, params: dict) -> np.ndarray:
        """Prime number interval pulsing."""
        primes = params.get("primes", PRIMES[:15])
        n_samples = int(self.sr * duration)
        signal = np.zeros(n_samples)
        
        t = 0
        idx = 0
        while t < duration and idx < len(primes):
            p = primes[idx]
            pulse_duration = min(0.1, p / 10.0)  # Short pulse
            start = int(t * self.sr)
            end = min(int((t + pulse_duration) * self.sr), n_samples)
            signal[start:end] = 1.0
            t += p
            idx += 1
        
        return to_iq_int8(signal, np.zeros_like(signal))
    
    def _fibonacci_sequence(self, duration: float, params: dict) -> np.ndarray:
        """Fibonacci sequence pulse intervals."""
        length = params.get("length", 12)
        
        # Generate Fibonacci sequence
        fib = [1, 1]
        for i in range(2, length):
            fib.append(fib[-1] + fib[-2])
        
        # Normalize to fit duration
        total = sum(fib)
        fib_scaled = [f / total * duration for f in fib]
        
        n_samples = int(self.sr * duration)
        signal = np.zeros(n_samples)
        
        t = 0
        for f in fib_scaled:
            if t >= duration:
                break
            pulse_duration = min(0.1, f / 2.0)
            start = int(t * self.sr)
            end = min(int((t + pulse_duration) * self.sr), n_samples)
            signal[start:end] = 1.0
            t += f
        
        return to_iq_int8(signal, np.zeros_like(signal))
    
    def _golden_ratio(self, duration: float, params: dict) -> np.ndarray:
        """Golden ratio (φ ≈ 1.618) modulated signal."""
        phi = (1 + np.sqrt(5)) / 2
        phi_periods = params.get("phi_periods", 5)
        
        # Modulate at phi Hz, phi² Hz, etc.
        t = np.linspace(0, duration, int(self.sr * duration), endpoint=False)
        signal = np.zeros_like(t)
        
        for n in range(1, phi_periods + 1):
            freq = phi ** n
            if freq > self.sr / 2:
                break
            signal += np.sin(2 * np.pi * freq * t) / n
        
        signal = normalise(signal)
        return to_iq_int8(signal, np.zeros_like(signal))
    
    def _chirp_up(self, duration: float, params: dict) -> np.ndarray:
        """Upward frequency chirp."""
        f_start = params.get("f_start", 500)
        f_end = params.get("f_end", 5000)
        
        sweep = chirp(f_start, f_end, duration, self.sr)
        return to_iq_int8(sweep, np.zeros_like(sweep))
    
    def _chirp_down(self, duration: float, params: dict) -> np.ndarray:
        """Downward frequency chirp."""
        f_start = params.get("f_start", 5000)
        f_end = params.get("f_end", 500)
        
        sweep = chirp(f_start, f_end, duration, self.sr)
        return to_iq_int8(sweep, np.zeros_like(sweep))
    
    def _silence(self, duration: float, params: dict) -> np.ndarray:
        """Silent probe (control)."""
        n_samples = int(self.sr * duration)
        return to_iq_int8(np.zeros(n_samples), np.zeros(n_samples))
    
    def custom_probe(self, waveform_fn: Callable, duration: float, 
                     description: str, kl_score: float = 1.0) -> Probe:
        """Create a custom probe from a waveform function.
        
        Parameters
        ----------
        waveform_fn : callable
            Function(duration, sr) -> (i_signal, q_signal) as numpy arrays.
        duration : float
            Probe duration in seconds.
        description : str
            Human-readable description.
        kl_score : float
            Expected KL divergence score.
        
        Returns
        -------
        Probe
            Custom probe configuration.
        """
        return Probe(
            type=ProbeType.CUSTOM,
            parameters={"waveform_fn": waveform_fn, "duration": duration},
            description=description,
            kl_score=kl_score,
        )

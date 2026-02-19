"""
Waveform generation primitives.
All functions return numpy float64 arrays normalised to [-1, 1].
"""

import numpy as np
from .constants import SCHUMANN_FREQUENCIES, PRIMES, AUDIO_SAMPLE_RATE


def sine(freq, duration, sr=AUDIO_SAMPLE_RATE):
    """Pure sine wave."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return np.sin(2 * np.pi * freq * t)


def am_modulate(carrier_freq, mod_freq, duration, depth=1.0, sr=AUDIO_SAMPLE_RATE):
    """Amplitude modulation: carrier modulated by mod_freq."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    carrier = np.sin(2 * np.pi * carrier_freq * t)
    modulator = 0.5 * (1 + depth * np.sin(2 * np.pi * mod_freq * t))
    return carrier * modulator


def schumann_envelope(duration, mode_weights=None, sr=AUDIO_SAMPLE_RATE):
    """
    Combined Schumann resonance envelope.
    Returns a low-frequency modulation signal combining all 5 modes.
    
    Args:
        mode_weights: dict {mode_number: weight} or None for equal weights
    """
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    if mode_weights is None:
        mode_weights = {1: 1.0, 2: 0.7, 3: 0.5, 4: 0.3, 5: 0.2}
    
    envelope = np.zeros_like(t)
    for mode, freq in enumerate(SCHUMANN_FREQUENCIES, 1):
        weight = mode_weights.get(mode, 0)
        envelope += weight * np.sin(2 * np.pi * freq * t)
    
    # Normalise to [0, 1] for use as modulation envelope
    envelope = (envelope - envelope.min()) / (envelope.max() - envelope.min())
    return envelope


def prime_pulse_gate(duration, sr=AUDIO_SAMPLE_RATE):
    """
    Prime number pulse gate: on for p_n seconds, off for p_{n+1} seconds.
    Returns array of 0s and 1s.
    """
    n_samples = int(sr * duration)
    gate = np.zeros(n_samples)
    
    t = 0
    prime_idx = 0
    on = True
    
    while t < duration and prime_idx < len(PRIMES):
        p = PRIMES[prime_idx % len(PRIMES)]
        start = int(t * sr)
        end = min(int((t + p) * sr), n_samples)
        
        if on:
            gate[start:end] = 1.0
        
        t += p
        on = not on
        prime_idx += 1
    
    return gate


def chirp(f_start, f_end, duration, sr=AUDIO_SAMPLE_RATE):
    """Linear frequency sweep."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    freq = f_start + (f_end - f_start) * (t / duration)
    phase = 2 * np.pi * np.cumsum(freq) / sr
    return np.sin(phase)


def breathing_envelope(duration, breath_rate=0.25, sr=AUDIO_SAMPLE_RATE):
    """Smooth breathing-like amplitude envelope."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return (0.5 * (1 + np.sin(2 * np.pi * breath_rate * t))) ** 2


def ping(freq, duration, interval, ping_length=0.05, sr=AUDIO_SAMPLE_RATE):
    """Periodic short pings at given frequency."""
    n_samples = int(sr * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    signal = np.zeros(n_samples)
    ping_samples = int(ping_length * sr)
    
    for start_time in np.arange(0, duration, interval):
        start_idx = int(start_time * sr)
        end_idx = min(start_idx + ping_samples, n_samples)
        if end_idx > start_idx:
            ping_t = t[start_idx:end_idx] - t[start_idx]
            envelope = np.exp(-ping_t * 40)
            signal[start_idx:end_idx] = np.sin(2 * np.pi * freq * t[start_idx:end_idx]) * envelope
    
    return signal


def normalise(signal, peak=0.9):
    """Normalise signal to [-peak, peak]."""
    max_val = np.max(np.abs(signal))
    if max_val > 0:
        return signal / max_val * peak
    return signal


def to_int16(signal):
    """Convert float64 signal to 16-bit PCM."""
    return np.int16(normalise(signal) * 32767)


def to_iq_int8(i_signal, q_signal=None):
    """Convert to interleaved IQ int8 for HackRF."""
    if q_signal is None:
        q_signal = np.zeros_like(i_signal)
    n = len(i_signal)
    iq = np.empty(n * 2, dtype=np.int8)
    iq[0::2] = np.int8(normalise(i_signal, 0.99) * 127)
    iq[1::2] = np.int8(normalise(q_signal, 0.99) * 127)
    return iq

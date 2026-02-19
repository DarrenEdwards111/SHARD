#!/usr/bin/env python3
"""
UAP Dog Whistle Audio Generator
Based on Jason Wilde's publicly shared specifications and
Enigmatic Ideas' Raspberry Pi implementation.

Generates a multi-layer WAV file with six distinct audio layers:
1. Schumann Resonance (7.83 Hz AM modulated over 100 Hz carrier)
2. Harmonic Tone (528 Hz with added harmonics)
3. High-Frequency Pings (17 kHz every 5 seconds)
4. Frequency Chirps (2.5 kHz sweeping upward every 10 seconds)
5. Ambient Pad (432 Hz with multiple harmonics)
6. Breathing White Noise (shaped to simulate breathing rhythm)

Usage: python3 uap3-generator.py [--duration 3600] [--output uap3_output.wav]
"""

import numpy as np
from scipy.io import wavfile
import argparse

SAMPLE_RATE = 44100


def generate_schumann_resonance(duration, sr):
    """Layer 1: 7.83 Hz Schumann resonance via AM modulation of 100 Hz carrier."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    carrier = np.sin(2 * np.pi * 100 * t)
    modulator = 0.5 * (1 + np.sin(2 * np.pi * 7.83 * t))
    return carrier * modulator * 0.3


def generate_harmonic_tone(duration, sr):
    """Layer 2: 528 Hz with harmonics for richness."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    fundamental = np.sin(2 * np.pi * 528 * t)
    harmonic2 = 0.5 * np.sin(2 * np.pi * 1056 * t)
    harmonic3 = 0.25 * np.sin(2 * np.pi * 1584 * t)
    harmonic4 = 0.125 * np.sin(2 * np.pi * 2112 * t)
    return (fundamental + harmonic2 + harmonic3 + harmonic4) * 0.15


def generate_high_freq_pings(duration, sr):
    """Layer 3: 17 kHz ultrasonic pings every 5 seconds."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    signal = np.zeros_like(t)
    ping_duration = 0.05  # 50ms ping
    ping_interval = 5.0   # every 5 seconds
    ping_samples = int(ping_duration * sr)

    for start_time in np.arange(0, duration, ping_interval):
        start_idx = int(start_time * sr)
        end_idx = min(start_idx + ping_samples, len(t))
        if end_idx > start_idx:
            ping_t = t[start_idx:end_idx] - t[start_idx]
            envelope = np.exp(-ping_t * 40)  # fast decay
            signal[start_idx:end_idx] = np.sin(2 * np.pi * 17000 * t[start_idx:end_idx]) * envelope

    return signal * 0.2


def generate_chirps(duration, sr):
    """Layer 4: 2.5 kHz chirps sweeping upward every 10 seconds."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    signal = np.zeros_like(t)
    chirp_duration = 0.3   # 300ms chirp
    chirp_interval = 10.0  # every 10 seconds
    chirp_samples = int(chirp_duration * sr)

    for start_time in np.arange(0, duration, chirp_interval):
        start_idx = int(start_time * sr)
        end_idx = min(start_idx + chirp_samples, len(t))
        if end_idx > start_idx:
            chirp_t = np.linspace(0, 1, end_idx - start_idx)
            freq_sweep = 2500 + 1500 * chirp_t  # sweep from 2.5 kHz to 4 kHz
            phase = 2 * np.pi * np.cumsum(freq_sweep) / sr
            envelope = np.sin(np.pi * chirp_t)  # smooth envelope
            signal[start_idx:end_idx] = np.sin(phase) * envelope

    return signal * 0.15


def generate_ambient_pad(duration, sr):
    """Layer 5: 432 Hz ambient pad with multiple harmonics."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    fundamental = np.sin(2 * np.pi * 432 * t)
    harmonic2 = 0.4 * np.sin(2 * np.pi * 864 * t)
    harmonic3 = 0.2 * np.sin(2 * np.pi * 1296 * t)
    harmonic5 = 0.1 * np.sin(2 * np.pi * 2160 * t)
    # Slow amplitude modulation for pad feel
    mod = 0.8 + 0.2 * np.sin(2 * np.pi * 0.1 * t)
    return (fundamental + harmonic2 + harmonic3 + harmonic5) * mod * 0.1


def generate_breathing_noise(duration, sr):
    """Layer 6: White noise shaped to simulate breathing rhythm."""
    n_samples = int(sr * duration)
    noise = np.random.randn(n_samples)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    # Breathing cycle: ~4 seconds inhale/exhale
    breath_envelope = 0.5 * (1 + np.sin(2 * np.pi * 0.25 * t))
    # Smooth the envelope
    breath_envelope = breath_envelope ** 2
    return noise * breath_envelope * 0.05


def main():
    parser = argparse.ArgumentParser(description='UAP Dog Whistle Audio Generator')
    parser.add_argument('--duration', type=int, default=3600, help='Duration in seconds (default: 3600 = 1 hour)')
    parser.add_argument('--output', type=str, default='uap3_output.wav', help='Output WAV filename')
    parser.add_argument('--sample-rate', type=int, default=44100, help='Sample rate (default: 44100)')
    args = parser.parse_args()

    sr = args.sample_rate
    duration = args.duration

    print(f"Generating UAP Dog Whistle signal ({duration}s at {sr} Hz)...")
    print("This may take a moment for long durations.\n")

    print("  [1/6] Schumann Resonance (7.83 Hz)...")
    layer1 = generate_schumann_resonance(duration, sr)

    print("  [2/6] Harmonic Tone (528 Hz)...")
    layer2 = generate_harmonic_tone(duration, sr)

    print("  [3/6] High-Frequency Pings (17 kHz)...")
    layer3 = generate_high_freq_pings(duration, sr)

    print("  [4/6] Frequency Chirps (2.5 kHz)...")
    layer4 = generate_chirps(duration, sr)

    print("  [5/6] Ambient Pad (432 Hz)...")
    layer5 = generate_ambient_pad(duration, sr)

    print("  [6/6] Breathing White Noise...")
    layer6 = generate_breathing_noise(duration, sr)

    print("\nMixing layers...")
    mixed = layer1 + layer2 + layer3 + layer4 + layer5 + layer6

    # Normalize to prevent clipping
    max_val = np.max(np.abs(mixed))
    if max_val > 0:
        mixed = mixed / max_val * 0.9

    # Convert to 16-bit PCM
    audio_16bit = np.int16(mixed * 32767)

    print(f"Writing {args.output}...")
    wavfile.write(args.output, sr, audio_16bit)

    file_size_mb = (len(audio_16bit) * 2) / (1024 * 1024)
    print(f"\nDone! Generated {args.output} ({file_size_mb:.1f} MB, {duration}s)")
    print("\nLayers:")
    print("  1. Schumann Resonance: 7.83 Hz AM modulated over 100 Hz carrier")
    print("  2. Harmonic Tone: 528 Hz with harmonics (1056, 1584, 2112 Hz)")
    print("  3. High-Frequency Pings: 17 kHz every 5 seconds")
    print("  4. Frequency Chirps: 2.5-4 kHz sweep every 10 seconds")
    print("  5. Ambient Pad: 432 Hz with harmonics (864, 1296, 2160 Hz)")
    print("  6. Breathing White Noise: 0.25 Hz breathing cycle")


if __name__ == '__main__':
    main()

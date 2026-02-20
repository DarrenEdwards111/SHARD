"""
Physical constants and configuration for the Hydrogen Line Beacon.
"""

# Hydrogen line — 21 cm spin-flip transition of neutral hydrogen
HYDROGEN_LINE_HZ = 1_420_405_751.768  # Hz (exact)
HYDROGEN_LINE_MHZ = 1420.405  # MHz

# Schumann resonance modes (Earth-ionosphere cavity)
SCHUMANN_MODES = {
    1: 7.83,    # fundamental — Earth circumference
    2: 14.3,    # 2nd harmonic
    3: 20.8,    # 3rd harmonic
    4: 27.3,    # 4th harmonic
    5: 33.8,    # 5th harmonic
}
SCHUMANN_FREQUENCIES = list(SCHUMANN_MODES.values())

# Water hole — quietest part of microwave spectrum
WATER_HOLE_LOW = 1.42e9    # Hydrogen (H)
WATER_HOLE_HIGH = 1.66e9   # Hydroxyl (OH)

# ISM bands (UK Ofcom licence-free)
ISM_BANDS = {
    '433': {'freq': 433.92e6, 'max_power_mw': 25, 'region': 'EU'},
    '868': {'freq': 868e6, 'max_power_mw': 500, 'region': 'EU'},
    '2400': {'freq': 2.4e9, 'max_power_mw': 100, 'region': 'Global'},
}

# Audio / DAC
AUDIO_SAMPLE_RATE = 44100
AUDIO_BIT_DEPTH = 16

# RF / HackRF
RF_SAMPLE_RATE = 2_000_000  # 2 MHz baseband
RF_DEFAULT_GAIN = 20        # dB TX gain (conservative)

# Prime number sequence for pulse timing
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
          53, 59, 61, 67, 71, 73, 79, 83, 89, 97]

# Protocol timing
PROTOCOL_TX_DURATION = 60    # seconds per transmit phase
PROTOCOL_RX_DURATION = 120   # seconds per listen phase
PROTOCOL_CYCLE_DURATION = 600  # seconds per full cycle

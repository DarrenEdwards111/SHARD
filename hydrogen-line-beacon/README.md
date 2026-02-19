# Hydrogen Line Beacon (HLB)

A dual-channel electromechanical signal system for the Raspberry Pi 5.

Two simultaneous channels, synchronised by a call-and-response protocol:

1. **RF Channel** — 1.42 GHz hydrogen line carrier, AM modulated with Earth's Schumann resonance series, prime-number pulse timing. Via HackRF One.
2. **Mechanical Channel** — Ground-coupled seismic transduction at Schumann frequencies (7.83–33.8 Hz) via DAC → amplifier → bass shaker → ground plate.

Based on the hypothesis described in [THEORY.md](../electromechanical/THEORY.md).

## Install

```bash
pip install -e .

# Or directly:
pip install numpy scipy
```

## Quick Start

```bash
# Mechanical channel only (no extra hardware needed beyond DAC + shaker)
hlb

# With RF (requires HackRF One)
hlb --rf

# ISM-legal RF (433 MHz, no licence needed)
hlb --rf --freq 433

# Hydrogen line (1.42 GHz, requires ham licence)
hlb --rf --freq hydrogen

# 30 minutes, pulsed programme
hlb --duration 1800 --programme pulsed

# Generate WAV file only
hlb --generate output.wav

# Check hardware
hlb --check

# Legal info
hlb --legal
```

## Python API

```python
from hlb import HydrogenLineBeacon

# Simple — mechanical only
beacon = HydrogenLineBeacon()
beacon.run()

# Full — both channels
beacon = HydrogenLineBeacon(rf=True, freq='hydrogen', duration=3600)
beacon.run()

# Just generate files
beacon.generate_mechanical("schumann.wav", duration=600, programme="pulsed")
beacon.generate_rf_baseband("baseband.iq", duration=60)

# Check what's connected
beacon.check_hardware()
```

### Individual Channels

```python
from hlb import MechanicalChannel, RFChannel, Monitor

# Mechanical
mech = MechanicalChannel()
mech.save_wav("ground.wav", programme="full", duration=3600)

# RF
rf = RFChannel(carrier_freq=1.420405e9)
rf.save_baseband("hydrogen.iq", duration=60, modulation="schumann", pulsed=True)

# Monitor
mon = Monitor(log_dir="./logs")
mon.capture_baseline(samples=5)
anomalies = mon.detect_anomalies(threshold_sigma=3.0)
```

### Protocol Controller

```python
from hlb import ProtocolController

controller = ProtocolController({
    'rf_enabled': True,
    'rf_carrier': 1.420405e9,
    'mech_programme': 'pulsed',
    'tx_duration': 60,
    'rx_duration': 120,
    'total_duration': 3600,
    'anomaly_threshold': 3.0,
})
controller.run()
```

## Programmes

| Programme | Description |
|-----------|-------------|
| `full` | Complete 10-min protocol cycle (recommended) |
| `pulsed` | All Schumann modes with prime-number pulse gating |
| `combined` | All 5 Schumann modes simultaneously |
| `fundamental` | 7.83 Hz only |
| `scan` | Step through each Schumann harmonic |
| `chirp` | Sweep 1–20 Hz |
| `breathing` | 7.83 Hz with breathing amplitude envelope |

## Hardware

### Minimum (Mechanical Only) — ~£130
- Raspberry Pi 5
- PCM5102A I2S DAC
- TPA3116D2 Class D amplifier
- Dayton Audio BST-1 bass shaker
- Ground plate + spike

### Full Build — ~£500
- Everything above, plus:
- HackRF One (RF TX/RX)
- RTL-SDR v4 (second receiver)
- Helical antenna (1.42 GHz)
- USB magnetometer
- Pi camera module
- Battery pack

See [electromechanical/README.md](../electromechanical/README.md) for full BOM and wiring.

## Package Structure

```
hlb/
├── __init__.py       — Package entry point
├── beacon.py         — HydrogenLineBeacon (high-level API)
├── cli.py            — Command-line interface
├── constants.py      — Physical constants and config
├── mechanical.py     — Ground transduction channel
├── monitor.py        — EM monitoring and anomaly detection
├── protocol.py       — Call-and-response state machine
├── rf.py             — HackRF RF transmission channel
└── waveforms.py      — Signal generation primitives
```

## Legal

- **433 MHz / 868 MHz ISM:** Licence-free in UK/EU at low power
- **1.42 GHz hydrogen line:** Requires amateur radio licence
- **Mechanical channel:** No restrictions (it's just vibration)
- Run `hlb --legal` for details

## Licence

MIT — Mikoshi Ltd, 2026

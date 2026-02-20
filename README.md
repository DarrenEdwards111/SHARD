# SHARD
## Schumann Hydrogen Active RF Discovery

A collection of experimental signal processing and RF transmission tools focused on Earth's electromagnetic environment, particularly Schumann resonances and the hydrogen line.

## Projects

### 🌍 Electromechanical Signal System

Dual-channel signal transmission combining RF and mechanical transduction for studying atmospheric electromagnetic phenomena.

**Location:** `electromechanical/`

A Raspberry Pi-based platform that:
- Broadcasts RF signals at configurable frequencies (including Schumann resonance harmonics)
- Couples low-frequency vibrations into the ground via bass shakers
- Explores the relationship between electromagnetic and seismic signal propagation

**Physics basis:**
- Schumann resonances (7.83 Hz fundamental, harmonics at 14.3, 20.8, 27.3, 33.8 Hz)
- Ground-coupled seismic transduction as an alternative to airborne acoustic transmission
- RF amplitude modulation with ELF patterns

See [electromechanical/README.md](electromechanical/README.md) and [electromechanical/THEORY.md](electromechanical/THEORY.md)

### 📡 Hydrogen Line Beacon

1420.405 MHz hydrogen line RF beacon with Schumann resonance modulation.

**Location:** `hydrogen-line-beacon/`

A dual-channel system transmitting on the universal hydrogen emission frequency:
- RF channel at 1.42 GHz (21 cm hydrogen line)
- Mechanical channel with ground-coupled Schumann frequencies
- Prime-number pulse timing for temporal structure
- Call-and-response monitoring protocol

**Features:**
- Python API and CLI (`hlb` command)
- Multiple transmission programmes (pulsed, combined, scan, chirp)
- Anomaly detection and EM monitoring
- Legal ISM band options (433/868 MHz) for testing

See [hydrogen-line-beacon/README.md](hydrogen-line-beacon/README.md), [hydrogen-line-beacon/BUILD-GUIDE.md](hydrogen-line-beacon/BUILD-GUIDE.md), and [hydrogen-line-beacon/FOL-ARRAY.md](hydrogen-line-beacon/FOL-ARRAY.md)

### 🔬 Active Discovery (APD Integration)

**NEW:** Sequential hypothesis testing for RF anomaly detection.

**Location:** `active-discovery/`

An experimental module that combines the Hydrogen Line Beacon with **Active Protocol Discovery (APD)** — a statistical framework for detecting adaptive responses to structured RF probes.

Instead of passively broadcasting a beacon, the Active Discovery system:
- **Adaptively selects** optimal probe signals (KL-divergence maximization)
- **Transmits** structured probes via HackRF One
- **Listens** for responses via RTL-SDR
- **Analyzes** responses for statistical anomalies
- **Decides** using Wald Sequential Probability Ratio Test (SPRT)

**Probe types:**
- Hydrogen line pulses (1420 MHz)
- Schumann-modulated carriers (7.83 Hz AM)
- Frequency sweeps
- Mathematical sequences (prime numbers, Fibonacci, golden ratio)
- Silence (control)

**Use cases:**
- RF anomaly detection with statistical rigor
- Active SETI experiments
- Ionospheric probing
- Adaptive radar waveform development

**Scientific basis:** Sequential hypothesis testing (Wald SPRT) applied to radio-frequency anomaly detection. The system can detect weak adaptive responses orders of magnitude faster than passive approaches, with controlled Type I/II error rates (typically α=0.01, β=0.01).

**Legal:** Requires amateur radio license for 1420 MHz. Can use ISM bands (433/868 MHz) without license.

See [active-discovery/README.md](active-discovery/README.md) for full documentation, hardware requirements, and usage examples.

## Physical Phenomena

### Schumann Resonances

The Schumann resonances are global electromagnetic resonances in the Earth-ionosphere cavity, excited by lightning discharges. The fundamental mode is 7.83 Hz, with harmonics approximately:

| Mode | Frequency (Hz) | Description |
|------|----------------|-------------|
| 1 | 7.83 | Fundamental |
| 2 | 14.3 | 2nd harmonic |
| 3 | 20.8 | 3rd harmonic |
| 4 | 27.3 | 4th harmonic |
| 5 | 33.8 | 5th harmonic |

These are actual atmospheric electromagnetic waves, not pseudoscience. They can be measured with sensitive magnetometers and VLF receivers.

### Hydrogen Line (21 cm)

The hydrogen line at 1420.405 MHz is the electromagnetic radiation spectral line emitted by neutral hydrogen atoms due to the hyperfine transition of the ground state. It's used in radio astronomy for mapping galactic hydrogen distribution and was included on the Pioneer plaque and Voyager Golden Record as a universal physical constant.

## Hardware Components

### RF Transmission
- HackRF One (1 MHz – 6 GHz SDR transceiver)
- RTL-SDR v4 (monitoring receiver)
- Antennas (discone, Yagi, helical for 1.42 GHz)
- RF amplifiers (optional, for increased range)

### Mechanical Transduction
- Raspberry Pi 5
- PCM5102A I2S DAC
- TPA3116D2 Class D amplifier
- Dayton Audio bass shakers (BST-1, TT25-8)
- Ground coupling plate + spike

### Monitoring
- USB magnetometers
- Pi camera modules
- Environmental sensors

## Legal Considerations (UK)

### RF Transmission
- **ISM bands (433 MHz, 868 MHz, 2.4 GHz):** Licence-free at low power (≤25 mW for 433, ≤500 mW for 868)
- **Amateur radio bands:** Require Foundation/Intermediate/Full amateur radio licence
- **1.42 GHz hydrogen line:** Requires amateur radio licence
- **Everything else:** Illegal to transmit without specific Ofcom authorisation

**Recommendation:** Start with 433 MHz ISM (legal, no licence required) or obtain a Foundation amateur radio licence (approximately £50, one-day course).

### Mechanical Channel
No restrictions — it's physical vibration. Safe levels are well below thresholds for human discomfort.

## Research Applications

- Studying Schumann resonance propagation characteristics
- Ground-coupled vs. airborne signal transmission efficiency
- RF modulation techniques with ELF patterns
- Seismic transduction for infrasound research
- Amateur radio experimentation on the hydrogen line
- Antenna design and testing for specific frequencies

## References & Further Reading

See PDFs in `electromechanical/` and `hydrogen-line-beacon/` directories for technical documentation, build guides, and theoretical background.

## Licence

MIT — Mikoshi Ltd, 2026

---

**Note:** This is experimental RF and signal processing work. Always comply with local radio regulations, maintain safe RF exposure distances, and respect the electromagnetic spectrum.

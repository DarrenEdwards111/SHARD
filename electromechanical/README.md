# Electromechanical UAP Dog Whistle

A combined RF transmitter + mechanical transducer system driven by a Raspberry Pi 5. Two signal channels, two physical mediums.

## Architecture

```
                    ┌─────────────────┐
                    │  Raspberry Pi 5 │
                    │                 │
                    │  Signal Gen     │
                    │  (Python/NumPy) │
                    └───────┬─────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
        ┌───────▼───────┐       ┌───────▼───────┐
        │  RF Channel   │       │  Mech Channel │
        │               │       │               │
        │  SPI/USB      │       │  I2S/DAC      │
        │  ↓            │       │  ↓            │
        │  HackRF One   │       │  Amplifier    │
        │  ↓            │       │  ↓            │
        │  RF Amp (opt) │       │  Bass Shaker  │
        │  ↓            │       │  ↓            │
        │  Antenna      │       │  Ground Plate │
        │               │       │               │
        │  EM Radiation │       │  Seismic Wave │
        └───────────────┘       └───────────────┘
```

## Channel 1: RF Transmission

Broadcasts electromagnetic signals at configurable frequencies.

### Hardware
| Component | Model | Est. Cost | Notes |
|-----------|-------|-----------|-------|
| SDR Transceiver | HackRF One | £250 | 1 MHz–6 GHz TX/RX |
| RF Amplifier | SPF5189Z LNA + PA | £15 | Optional, boosts output |
| Antenna (wideband) | Discone or log-periodic | £30–80 | Covers 25 MHz–6 GHz |
| Antenna (directional) | Yagi for target freq | £20–50 | Higher gain, narrower beam |
| SMA cables & adapters | Various | £15 | SMA to antenna |

### Frequencies of Interest
| Frequency | Band | Relevance |
|-----------|------|-----------|
| 1.6 GHz | L-Band | Skinwalker Ranch correlation |
| 1.42 GHz | Hydrogen line | Universal hydrogen emission |
| 433 MHz | ISM (UK legal) | LoRa/Meshtastic band, licence-free |
| 868 MHz | ISM (UK legal) | European ISM, licence-free |
| 7.83 Hz | ELF | Schumann resonance (RF, not audio) |
| 14.3 Hz | ELF | 2nd Schumann harmonic |

### ⚠️ Legal (UK — Ofcom)
- **ISM bands (433 MHz, 868 MHz, 2.4 GHz):** Licence-free at low power (≤25 mW for 433, ≤500 mW for 868)
- **Amateur bands:** Require Foundation/Intermediate/Full ham licence
- **Everything else:** Illegal to transmit without specific authorisation
- **Recommendation:** Start with 433 MHz ISM (legal, no licence) or get a Foundation ham licence (£50, one-day course)

### Software
Uses `hackrf_transfer` or GNU Radio for signal generation. The Pi generates the baseband waveform, HackRF handles RF upconversion.

## Channel 2: Mechanical Transduction

Couples low-frequency vibrations directly into the physical environment (ground, structures, water).

### Hardware
| Component | Model | Est. Cost | Notes |
|-----------|-------|-----------|-------|
| DAC | PCM5102A I2S board | £8 | 32-bit, 384 kHz, connects to Pi GPIO |
| Amplifier | TPA3116D2 Class D | £12 | 50W–100W, efficient |
| Bass Shaker (primary) | Dayton Audio BST-1 | £25 | 10W, 20–80 Hz response |
| Bass Shaker (heavy) | Dayton Audio TT25-8 | £15 | Puck transducer, bolt-mount |
| Ground Plate | 400mm aluminium disc | £20 | 6mm thick, bolted to shaker |
| Ground Spike | Steel rod, 300mm | £5 | Couples plate to earth |
| Speaker wire | 14 AWG | £8 | Shaker to amp |

### How Mechanical Transduction Works

A bass shaker is a speaker without a cone. Instead of pushing air, it vibrates whatever surface it's bolted to. By mounting it on a metal plate spiked into the ground:

1. **Pi generates waveform** → digital signal at exact frequency
2. **DAC converts** → analogue audio signal
3. **Amplifier boosts** → enough power to drive the shaker (10–50W)
4. **Bass shaker vibrates** → converts electrical signal to physical motion
5. **Ground plate transfers** → vibration into the earth
6. **Ground spike couples** → direct contact with soil for maximum transfer

This can reproduce frequencies a speaker physically cannot:
- **7.83 Hz** Schumann resonance — as actual ground vibration
- **14.3 Hz** 2nd Schumann harmonic
- **1–5 Hz** infrasound range — felt, not heard

### Why Ground Coupling?

Normal speakers move air. Below ~20 Hz, speakers are essentially useless — the wavelengths are too long. But seismic/infrasound waves travel efficiently through the ground. The Earth itself resonates at 7.83 Hz (Schumann resonance is an EM phenomenon, but the mechanical analogue is equally valid as a transmission medium).

Seismic waves propagate further than airborne sound at these frequencies and cannot be blocked by walls, buildings, or terrain.

## Combined Signal Spec

Both channels fire simultaneously, synchronised by the Pi's clock.

### Default Programme
| Time | RF Channel | Mechanical Channel |
|------|-----------|-------------------|
| 0:00–0:30 | 433 MHz carrier, 7.83 Hz AM modulation | 7.83 Hz pure tone (Schumann) |
| 0:30–1:00 | 433 MHz carrier, 14.3 Hz AM modulation | 14.3 Hz (2nd Schumann) |
| 1:00–2:00 | 433 MHz, pulsed (1s on / 1s off) | 7.83 Hz + 14.3 Hz combined |
| 2:00–3:00 | 868 MHz carrier, 7.83 Hz AM | Chirp sweep 1–20 Hz |
| 3:00–5:00 | Frequency hop: 433→868→1420 MHz (10s each) | Breathing pattern, 7.83 Hz base |
| 5:00–10:00 | Repeat cycle | Repeat cycle |

### Synchronisation
Both channels share a common timebase from the Pi's system clock. The Python controller spawns two threads — one for RF, one for mechanical — both referenced to `time.monotonic()` for drift-free sync.

## Bill of Materials

### Minimum Viable Build (£100)
| Item | Cost |
|------|------|
| Raspberry Pi 5 (4GB) | £50 |
| PCM5102A DAC | £8 |
| TPA3116D2 amp | £12 |
| Dayton BST-1 bass shaker | £25 |
| Ground plate + spike | £25 |
| Wiring, connectors | £10 |
| **Total** | **£130** |

This gets you the mechanical channel only. Legal, no licence needed.

### Full Build (£400)
| Item | Cost |
|------|------|
| Raspberry Pi 5 (4GB) | £50 |
| HackRF One | £250 |
| Discone antenna | £40 |
| PCM5102A DAC | £8 |
| TPA3116D2 amp | £12 |
| Dayton BST-1 bass shaker | £25 |
| Ground plate + spike | £25 |
| PiSugar / USB-C battery | £30 |
| Pelican-style case | £30 |
| Wiring, SMA cables | £25 |
| **Total** | **~£495** |

Both channels, portable, field-ready. Requires ham licence for non-ISM RF frequencies.

## GPIO Pinout (Pi 5)

```
RF Channel (HackRF One):
  USB-C or USB 3.0 → Pi USB port

Mechanical Channel (I2S DAC):
  BCK  → GPIO 18 (Pin 12)
  LRCK → GPIO 19 (Pin 35)
  DIN  → GPIO 21 (Pin 40)
  VIN  → 3.3V (Pin 1)
  GND  → GND (Pin 6)

Amplifier:
  DAC line out → TPA3116D2 input
  TPA3116D2 output → Bass shaker terminals
  TPA3116D2 power → 12V DC supply or battery
```

## Safety

- **RF exposure:** Keep antenna >2m from people during transmission. Low power ISM is safe at distance.
- **Infrasound:** Prolonged exposure to high-amplitude infrasound (>120 dB) can cause nausea, disorientation. Our levels are well below this (~60–80 dB at source).
- **Skywatcher's warning:** They report historic injuries from UAP proximity including radiation and directed energy. If you attract something, keep distance. Bring a dosimeter if you're serious.
- **Legal:** Do not transmit outside ISM bands without a licence. Ofcom enforcement is real.

## Further Research
- Skinwalker Ranch L-Band (1.6 GHz) experiments
- Schumann resonance monitoring stations
- Infrasound detection arrays (CTBTO network)
- CE-5 / Steven Greer contact protocols (consciousness-based, no hardware)
- James Fowler's Skywatcher interviews on signal methodology

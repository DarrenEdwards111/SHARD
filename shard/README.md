# Active Discovery — APD-Driven Hydrogen Line Beacon

**Active Protocol Discovery (APD) integration for the Hydrogen Line Beacon (HLB)**

This module combines the HLB RF transmission system with Active Protocol Discovery for **sequential hypothesis testing of radio-frequency anomaly responses**. Instead of passively broadcasting a beacon, the active discovery system adaptively selects optimal probes, transmits them, listens for responses, and uses sequential probability ratio testing (SPRT) to detect statistically significant deviations from background noise.

---

## Concept: Active vs Passive Discovery

### Passive Discovery (Traditional Beacon)
- Transmits a **fixed signal** continuously or periodically
- Hopes for a response but has no mechanism to optimize signal selection
- Cannot distinguish adaptive responses from random noise without extensive data collection
- Used by: SETI, Voyager Golden Record, Arecibo message

### Active Discovery (This Module)
- Uses **Active Protocol Discovery (APD)** — a sequential statistical framework
- **Adaptively selects** the next probe based on maximum information gain (KL-divergence)
- **Listens** for responses after each probe
- **Updates a sequential hypothesis test** (Wald SPRT) with each observation
- **Decides** whether a response is adaptive or noise with rigorous error bounds (α, β)

**Key advantage**: Active discovery can detect weak adaptive responses **orders of magnitude faster** than passive approaches, with statistically rigorous false positive/negative rates.

---

## How It Works: The Probe-Listen-Adapt Loop

```
┌─────────────────────────────────────────────────┐
│  1. SELECT PROBE (APD Policy)                   │
│     - KL-optimal: maximizes information gain    │
│     - Chooses from probe library                │
└─────────────────┬───────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│  2. TRANSMIT PROBE (HackRF via HLB)             │
│     - Hydrogen line (1420.405 MHz)              │
│     - ISM bands (433/868/2400 MHz)              │
│     - Structured signal (see Probe Library)     │
└─────────────────┬───────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│  3. INTER-PROBE DELAY                           │
│     - Brief silence for settling                │
└─────────────────┬───────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│  4. LISTEN FOR RESPONSE (RTL-SDR)               │
│     - Capture IQ samples                        │
│     - Duration: typically 3× probe duration     │
└─────────────────┬───────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│  5. ANALYZE RESPONSE                            │
│     - Power spectral density                    │
│     - Cross-correlation with probe              │
│     - Anomaly detection (σ threshold)           │
└─────────────────┬───────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│  6. UPDATE SPRT                                 │
│     - Compute log-likelihood ratio (LLR)        │
│     - Accumulate evidence for H1 vs H0          │
│     - Check decision thresholds                 │
└─────────────────┬───────────────────────────────┘
                  ▼
         ┌────────┴────────┐
         │  Decision?      │
         └────────┬────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
       Yes                 No
        │                   │
        ▼                   ▼
  ┌─────────┐         ┌──────────┐
  │ H1: Adaptive │    │ Continue │
  │ H0: Null    │     │ loop     │
  └─────────┘         └──────────┘
```

### Hypothesis Test
- **H₀ (Null)**: Observed signal is background noise (no adaptive response)
- **H₁ (Adaptive)**: Observed signal shows statistically significant deviation correlated with probe transmission

**SPRT** (Sequential Probability Ratio Test) accumulates evidence until one of two error-controlled thresholds is crossed:
- **α** (Type I error): False positive rate — detecting adaptive response when none exists
- **β** (Type II error): False negative rate — missing adaptive response

Typical settings: `α = 0.01`, `β = 0.01` (99% confidence in both directions)

---

## Probe Library

The system includes a library of **structured probe signals**, each designed to maximize information content and test different hypothesized response mechanisms:

| Probe Type | Description | Use Case |
|------------|-------------|----------|
| **Hydrogen Pulse** | Pulsed carrier on 1420.405 MHz with prime-number gating | Test for response to neutral hydrogen line |
| **Schumann AM** | Amplitude modulation at Schumann resonances (7.83 Hz fundamental) | Test for response to Earth-ionosphere cavity frequencies |
| **Frequency Sweep** | Linear chirp across baseband range | Identify frequency-dependent responses |
| **Prime Sequence** | Pulses spaced by prime number intervals (2, 3, 5, 7...) | Test for recognition of mathematical structure |
| **Fibonacci Sequence** | Pulses spaced by Fibonacci intervals | Test for recognition of natural growth sequences |
| **Golden Ratio** | Modulation at φ, φ², φ³... (φ ≈ 1.618) | Test for response to fundamental mathematical constants |
| **Silence** | No transmission (control probe) | Baseline measurement |

Each probe is assigned a **KL score** (Kullback-Leibler divergence) indicating its expected information gain. The APD policy selects the probe with maximum KL score at each iteration.

---

## Integration with Hydrogen Line Beacon

This module **extends** the HLB codebase:

```
hydrogen-line-beacon/
  hlb/
    beacon.py      ← HLB transmitter (used by active_beacon.py)
    waveforms.py   ← Waveform generation (used by probe_library.py)
    rf.py          ← HackRF control (used by active_beacon.py)
    monitor.py     ← RTL-SDR reception (used by active_beacon.py)
    constants.py   ← Physical constants (imported everywhere)

active-discovery/
  active_beacon.py     ← Main APD loop (imports HLB modules)
  probe_library.py     ← Probe generation (uses hlb.waveforms)
  response_analyzer.py ← Signal analysis
  config.py            ← Configuration
```

**Key imports**:
- `hlb.rf.RFChannel` — HackRF transmission
- `hlb.monitor.Monitor` — RTL-SDR reception
- `hlb.waveforms` — Waveform primitives
- `apd.APDEngine`, `apd.WaldSPRT`, `apd.KLOptimalPolicy` — APD framework

---

## Hardware Requirements

### Essential
- **HackRF One** — SDR transceiver for RF transmission
  - Frequency range: 1 MHz – 6 GHz
  - Sample rate: up to 20 MS/s
  - TX power: ~10 dBm (10 mW)
  - [£250–300, hackrf.com](https://greatscottgadgets.com/hackrf/)

- **RTL-SDR** — Low-cost SDR receiver for response monitoring
  - Frequency range: 24 MHz – 1.7 GHz (with upconverter can reach HF)
  - [£25–40, rtl-sdr.com](https://www.rtl-sdr.com/)

- **Antenna** — Tuned for target frequency
  - Hydrogen line (1420 MHz): 21 cm dipole or helical
  - 433 MHz: Quarter-wave monopole (~17 cm)
  - 868 MHz: Quarter-wave monopole (~8.6 cm)

### Optional
- **RF Amplifier** — Boost TX power (stay within legal limits!)
- **Directional Antenna** — Yagi or parabolic for focused beam
- **RF Filters** — Band-pass filters to reduce harmonics

---

## Legal Considerations

### ⚠️ **CRITICAL: Transmission Licensing**

**Unlicensed transmission on most frequencies is illegal in the UK and most jurisdictions.**

#### Safe Options (UK/EU):
**ISM Bands** — No license required:
- **433.92 MHz** — Max 25 mW ERP
- **868 MHz** — Max 500 mW ERP
- **2.4 GHz** — Max 100 mW ERP

**Configure for ISM**:
```python
config = APDConfig(
    carrier_freq=433.92e6,  # 433 MHz ISM
    tx_gain=14,             # ~25 mW
)
```

#### Licensed Option:
**Hydrogen Line (1420.405 MHz)** — **Requires amateur radio license**:
- **UK**: Foundation License (one-day course, ~£50, Ofcom)
- **US**: Technician License (FCC)
- **EU**: CEPT harmonized license

**Configure for hydrogen line** (after obtaining license):
```python
config = APDConfig(
    carrier_freq=1420.405751768e6,  # Hydrogen line
    tx_gain=20,                     # 100 mW
    require_ham_license_confirm=False,  # YOU confirm you have a license
)
```

**DO NOT TRANSMIT ON 1420 MHz WITHOUT A LICENSE.**

The code includes a safety check that will abort if `carrier_freq` is near 1420 MHz and `require_ham_license_confirm=True`.

---

## Installation & Usage

### Install Dependencies
```bash
# APD framework
cd /path/to/active-protocol-discovery
pip install -e .

# HLB dependencies (if not already installed)
pip install numpy scipy

# Hardware tools
sudo apt install hackrf rtl-sdr
```

### Basic Usage

```python
from active_discovery import ActiveBeacon, APDConfig

# Configure for ISM band (legal, no license)
config = APDConfig(
    carrier_freq=433.92e6,       # 433 MHz ISM
    max_iterations=50,           # Stop after 50 probes or decision
    probe_duration=5.0,          # 5 seconds per probe
    listen_duration=15.0,        # 15 seconds listen window
    inter_probe_delay=10.0,      # 10 seconds between probes
    sprt_alpha=0.01,             # 1% false positive rate
    sprt_beta=0.01,              # 1% false negative rate
    log_dir="./apd_logs",
)

# Create beacon
beacon = ActiveBeacon(config, verbose=True)

# Check hardware
hw_status = beacon.check_hardware()
if not hw_status["ready"]:
    print("Missing hardware!")
    exit(1)

# Run APD session
result = beacon.run()

# Interpret result
if result.decision == 1:
    print(f"✓ Adaptive response detected after {result.steps} probes")
elif result.decision == 0:
    print(f"✗ No adaptive response (null hypothesis) after {result.steps} probes")
else:
    print(f"? Undecided after {result.steps} probes (max iterations reached)")
```

### Command-Line Interface

```bash
# ISM band (433 MHz)
python -m active_discovery.active_beacon --freq 433.92e6 --max-iter 50

# Hydrogen line (requires license!)
python -m active_discovery.active_beacon --hydrogen --max-iter 100

# Custom parameters
python -m active_discovery.active_beacon \
    --freq 868e6 \
    --max-iter 30 \
    --probe-duration 3.0 \
    --listen-duration 10.0 \
    --log-dir ./my_logs
```

---

## Output & Logging

Each session generates:

1. **Iteration log** (`<session_id>_iterations.jsonl`):
   - One JSON line per probe-response cycle
   - Includes probe type, response metrics, SPRT state

2. **Summary** (`<session_id>_summary.json`):
   - Final decision (H0/H1)
   - Total steps
   - Configuration
   - Hardware status

3. **Raw IQ files** (in `temp_dir`):
   - `probe_<N>.iq` — Transmitted probe IQ
   - `response_<N>.iq` — Captured response IQ

**Example iteration log entry**:
```json
{
  "session_id": "20250220_123045",
  "iteration": 3,
  "timestamp": "2025-02-20T12:31:15.234567",
  "probe": {
    "type": "schumann_am",
    "description": "AM modulated by Schumann resonances",
    "kl_score": 3.0
  },
  "response": {
    "power_mean": 1.23e-5,
    "power_std": 3.45e-6,
    "snr_db": 12.3,
    "anomaly_score": 2.1,
    "correlation": 0.15,
    "is_anomaly": false
  },
  "sprt": {
    "llr": -0.45,
    "cumulative_log_odds": -1.23,
    "decision": null,
    "steps": 4
  }
}
```

---

## Scientific Context

This is a **novel application** of sequential hypothesis testing to radio astronomy / atmospheric RF monitoring. The framework is designed for:

1. **UAP/Anomaly Research** — Detecting adaptive responses to structured RF probes
2. **SETI** — Active messaging with statistical rigor
3. **Atmospheric Physics** — Probing ionospheric phenomena (Schumann resonances, sprites)
4. **Radar Development** — Adaptive waveform optimization

The method is **agnostic** to the source of adaptive response. It simply asks:
> "Does the environment respond non-randomly to structured probes?"

If yes → H₁ (adaptive)  
If no → H₀ (null)

---

## References

- **Active Protocol Discovery**: [github.com/your-repo/active-protocol-discovery](https://github.com/DarrenEdwards111/active-protocol-discovery)
- **Wald SPRT**: Wald, A. (1945). "Sequential Tests of Statistical Hypotheses"
- **Hydrogen Line**: 21 cm spin-flip transition of neutral hydrogen (1420.405751768 MHz)
- **Schumann Resonances**: Earth-ionosphere cavity modes (~7.83 Hz fundamental)
- **HackRF One**: [greatscottgadgets.com/hackrf](https://greatscottgadgets.com/hackrf/)
- **RTL-SDR**: [rtl-sdr.com](https://www.rtl-sdr.com/)

---

## Safety & Ethics

- **Legal compliance**: Only transmit on frequencies you are licensed to use
- **RF exposure**: Keep TX power low (≤100 mW) and antennas away from people
- **Interference**: Avoid frequencies used by emergency services, aviation, etc.
- **Scientific integrity**: Log all data, publish methods transparently
- **Responsible disclosure**: If you detect anomalous responses, document rigorously before making claims

**This is experimental research. Results are not evidence of anything without reproducibility and peer review.**

---

## License

Same as parent repository (MIT or Apache 2.0, depending on UAP_Dog_Whistle license).

---

## Author

Darren Edwards ([@DarrenEdwards111](https://github.com/DarrenEdwards111))

**Contributions welcome!** This is an open research project.

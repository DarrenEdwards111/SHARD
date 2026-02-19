# Flower-of-Life Transducer Array (Advanced, Optional)

*Applying FoL hexagonal geometry to multi-transducer ground coupling.*

**Mikoshi Ltd — February 2026**

**Status:** Theoretical extension. Single-transducer build works fine. This is for experimenters who want to push further.

---

## Background

The Flower of Life is a geometric pattern of overlapping circles arranged in hexagonal symmetry. In Edwards (2026) [1], the FoL tiling is used as a cell design for proving global regularity of the 3D Navier–Stokes equations. The key property exploited is **monopole cancellation at cell boundaries** — far-field stretching terms cancel due to the hexagonal symmetry, while a logistic control inequality prevents blow-up.

The same geometric properties apply to wave propagation: multiple sources arranged in a FoL pattern produce constructive interference at specific points while cancelling energy that would otherwise leak laterally. This is geometrically-driven beam-forming — a phased array without electronics.

## Where This Helps (and Where It Doesn't)

### Genuinely useful: Mid-frequency seismic (50–200 Hz)

At 100 Hz through soil (propagation speed ~500 m/s), the wavelength is ~5m. A FoL array of 7 transducers spaced 3–5m apart spans roughly one wavelength. This is the sweet spot: the array is physically buildable and produces meaningful constructive interference downward into the earth.

- Wavelength matches array scale
- Hexagonal symmetry creates directional coupling into ground
- Logistic stability means the interference pattern is self-regulating
- 7 transducers is manageable (1 centre + 6 ring)

### Theoretically beautiful but impractical: Schumann frequencies (7.83 Hz)

At 7.83 Hz through soil, the wavelength is ~60m. A FoL array would need to span ~60m across. That's a football pitch of ground plates and shakers. Not impossible, but far beyond a portable build.

- The single-transducer design works fine at these frequencies
- A point source at 7.83 Hz already couples efficiently because the wavelength is so long relative to any near-field structure
- The array gain wouldn't justify the cost and complexity

### Not meaningfully better: RF (1.42 GHz)

At 1.42 GHz, wavelength is 21 cm. A FoL array of antennas would need ~1m diameter — physically feasible. But a single helical antenna already provides 12+ dBi gain with circular polarisation. An array adds complexity (phasing, matching) for modest improvement. If you want more RF gain, just build a bigger dish or a longer helix.

## The FoL Array Design (7 Transducers)

### Geometry

```
         [2]
        / | \
      /   |   \
    [3]---[1]---[6]
      \   |   /
        \ | /
         [4]       [5] and [7] behind/in front (3D hexagonal)
```

Top-down view of the Flower of Life first ring:

```
            ○ T2
           / \
          /   \
    T3 ○─────○ T1 (centre)─────○ T6
          \   /
           \ /
            ○ T4
           / \
          /   \
    T7 ○─────○─────○ T5
```

Actual FoL pattern (overlapping circles, centres marked):

```
        ·  ○  ·
       ○  [2]  ○
      ·  ○  ·  ○  ·
     ○  [3]  [1]  [6]  ○
      ·  ○  ·  ○  ·
       ○  [4]  ○
        ·  ○  ·
           [5]
```

Each ○ represents a transducer position. Spacing between adjacent transducers = r, where r is chosen based on target frequency:

| Target Frequency | Soil Wavelength (~500 m/s) | Array Spacing (r) | Total Array Diameter |
|-----------------|---------------------------|-------------------|---------------------|
| 200 Hz | 2.5 m | 1.2 m | ~2.5 m |
| 100 Hz | 5 m | 2.5 m | ~5 m |
| 50 Hz | 10 m | 5 m | ~10 m |
| 20 Hz | 25 m | 12 m | ~25 m |
| 7.83 Hz | 64 m | 32 m | ~64 m |

**Recommended: 100 Hz, r = 2.5m.** Fits in a garden. Meaningful array effects. Audible as a low hum (useful for confirming it's working).

### Hardware (7-Transducer Array)

| # | Item | Qty | Unit Cost | Total |
|---|------|-----|-----------|-------|
| 1 | Dayton Audio BST-1 bass shaker | 7 | £25 | £175 |
| 2 | 400mm aluminium ground plates | 7 | £20 | £140 |
| 3 | 300mm steel ground spikes | 7 | £5 | £35 |
| 4 | TPA3116D2 4-channel amp | 2 | £15 | £30 |
| 5 | 14 AWG speaker wire (50m) | 1 | £15 | £15 |
| 6 | 12V LiFePO4 battery (20Ah) | 1 | £80 | £80 |
| 7 | M4 mounting hardware | 7 sets | £3 | £21 |
| | | | **Total** | **~£496** |

Plus the Pi 5 and DAC from the base build (~£70). Grand total for mechanical FoL array: **~£566**.

### Wiring

The Pi has one I2S output (stereo = 2 channels). To drive 7 transducers independently you need either:

**Option A: All in phase (simple)**
Wire all 7 shakers in parallel from one amplifier. They all play the same signal simultaneously. The FoL geometry does the beam-forming passively.

```
Pi I2S → DAC → Amp Ch1 →┬→ T1 (centre)
                         ├→ T2
                         ├→ T3
                         ├→ T4
                         ├→ T5
                         ├→ T6
                         └→ T7
```

Impedance: 7× BST-1 (8Ω each) in parallel = 1.14Ω. The TPA3116D2 handles down to 2Ω, so wire them in series-parallel groups:

```
Group A (series): T1 + T2 + T3 = 24Ω
Group B (series): T4 + T5 + T6 = 24Ω
Group C: T7 alone = 8Ω

Groups A and B in parallel = 12Ω
Then A||B in parallel with C = (12 × 8)/(12 + 8) = 4.8Ω ✓
```

**Option B: Phase-controlled (advanced)**
Use a multi-channel USB audio interface (e.g. Behringer UMC1820, 8 outputs, ~£180) to drive each transducer with independent phase offsets. This enables active beam-steering — pointing the constructive interference in different directions.

This is significantly more complex and expensive. Only worth it if you're serious about directional ground coupling.

### Signal Design for the Array

For the all-in-phase configuration, the standard HLB signals work unmodified. The geometry handles everything.

For experimentation, consider:

**1. Dual-frequency mode**
Centre transducer (T1) runs 7.83 Hz Schumann fundamental.
Ring transducers (T2–T7) run 100 Hz carrier AM-modulated with 7.83 Hz.

The 100 Hz carrier benefits from the array geometry (wavelength matches spacing). The 7.83 Hz modulation rides on top. You get both: efficient array coupling at 100 Hz and the Schumann signature embedded in the envelope.

**2. Sequential activation**
Instead of all transducers simultaneously, activate them in FoL order: centre first, then ring clockwise. One full rotation per Schumann cycle (every 128ms for 7.83 Hz). This creates a rotating wave pattern in the ground — a mechanical analogue of circular polarisation.

**3. Prime-pulse per transducer**
Each transducer gets its own prime from the sequence: T1=2s, T2=3s, T3=5s, T4=7s, T5=11s, T6=13s, T7=17s. The combined pattern is unique and unmistakably artificial from any detection point.

## The Physics: Why Hexagonal Symmetry Matters

From Edwards (2026) [1], the FoL cell design has three properties relevant to wave transmission:

### 1. Monopole cancellation at cell boundaries

In the Navier–Stokes context, the vortex stretching term — which threatens blow-up — cancels at FoL cell boundaries due to hexagonal symmetry. In wave transmission terms: energy that would radiate laterally from each source is cancelled by the adjacent sources. The net effect is that energy is redirected vertically (into the ground) rather than spreading horizontally.

This is the same principle as a phased array, but achieved through geometry rather than electronic phase control. The FoL arrangement is the natural geometry that produces this cancellation.

### 2. Logistic control (self-stabilising interference)

The FoL crystal capacity C(t) obeys:

```
dC/dt ≤ rC(1 - C/K) + error terms
```

This is a logistic inequality — it has a carrying capacity K and cannot blow up. For a transducer array, this means the constructive interference pattern is **self-limiting**. You won't get destructive resonance build-up that damages equipment or creates unpredictable field patterns. The hexagonal geometry inherently stabilises the interference.

### 3. Dyadic vorticity hierarchy

The FoL weights w_n ~ 2^{(2/3)n} create a multi-scale structure. For a transducer array, this suggests that operating at multiple harmonically related frequencies simultaneously (e.g. 50 Hz, 100 Hz, 200 Hz) would produce a coherent multi-scale ground penetration pattern — each frequency reaching a different depth, all geometrically coherent.

## Honest Assessment

**What the FoL array adds:**
- Real constructive interference at 50–200 Hz (physics is solid)
- Self-stabilising field pattern (logistic bound)
- More total power into the ground (7× transducers)
- A geometrically unique signal signature

**What it doesn't add:**
- No meaningful improvement at 7.83 Hz (wavelength too long for any buildable array)
- No improvement to the RF channel
- Significant cost and complexity vs single transducer

**Who should build this:**
- People who've already built the basic beacon and want to experiment further
- Researchers interested in seismic array effects
- Anyone with a large flat field and ~£500 spare

**Who should skip this:**
- First-time builders (start with single transducer)
- Anyone without space for a 5m+ array
- Anyone primarily interested in the RF channel

## References

[1] Edwards, D.J. (2026). "An Unconditional Proof of Global Regularity for the 3D Navier–Stokes Equations in ZFC via Flower-of-Life Cell Design and SPDP Complexity." Zenodo. doi:10.5281/zenodo.18116340

---

*Mikoshi Ltd, 2026 — MIT Licence*

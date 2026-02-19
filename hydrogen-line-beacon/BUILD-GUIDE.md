# Hydrogen Line Beacon — Complete Build Guide

*Full hardware assembly, wiring, and deployment instructions.*

**Mikoshi Ltd — February 2026**

---

## Table of Contents

1. [Overview](#1-overview)
2. [Bill of Materials](#2-bill-of-materials)
3. [Tier 1: Mechanical Only Build](#3-tier-1-mechanical-only-build)
4. [Tier 2: Full Build (RF + Mechanical)](#4-tier-2-full-build)
5. [Raspberry Pi 5 Setup](#5-raspberry-pi-5-setup)
6. [Software Installation](#6-software-installation)
7. [Channel 1: Mechanical Assembly](#7-channel-1-mechanical-assembly)
8. [Channel 2: RF Assembly](#8-channel-2-rf-assembly)
9. [Monitoring Station Assembly](#9-monitoring-station-assembly)
10. [Field Deployment](#10-field-deployment)
11. [Operating Procedures](#11-operating-procedures)
12. [Troubleshooting](#12-troubleshooting)
13. [Safety](#13-safety)

---

## 1. Overview

### What We're Building

A portable, field-deployable dual-channel signal system controlled by a Raspberry Pi 5:

```
┌─────────────────────────────────────────────────────────────┐
│                    RASPBERRY PI 5                            │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Protocol │  │ Waveform │  │ Monitor  │  │  Logger   │  │
│  │ Engine   │  │ Generator│  │ (SDR RX) │  │ (JSON)    │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────────┘  │
│       │              │              │                        │
└───────┼──────────────┼──────────────┼────────────────────────┘
        │              │              │
   ┌────▼────┐    ┌────▼────┐   ┌────▼────┐
   │ USB 3.0 │    │  I2S    │   │ USB 2.0 │
   └────┬────┘    └────┬────┘   └────┬────┘
        │              │              │
   ┌────▼────┐    ┌────▼────┐   ┌────▼────┐
   │ HackRF  │    │PCM5102A │   │ RTL-SDR │
   │  One    │    │  DAC    │   │   v4    │
   └────┬────┘    └────┬────┘   └────┬────┘
        │              │              │
   ┌────▼────┐    ┌────▼────┐   ┌────▼────┐
   │Helical  │    │TPA3116  │   │Discone  │
   │Antenna  │    │  Amp    │   │Antenna  │
   │(TX)     │    └────┬────┘   │(RX)     │
   └─────────┘    ┌────▼────┐   └─────────┘
                  │  Bass   │
        EM        │ Shaker  │      EM
      Radiation   └────┬────┘   Reception
                  ┌────▼────┐
                  │ Ground  │
                  │  Plate  │
                  └────┬────┘
                  ┌────▼────┐
                  │ Ground  │
                  │  Spike  │
                  └─────────┘
                   Seismic
                    Wave
```

### What Goes Where

| Component | Connects To | Channel | Purpose |
|-----------|-------------|---------|---------|
| Raspberry Pi 5 | Everything | Controller | Runs all software |
| HackRF One | Pi USB 3.0 | RF TX | Transmits hydrogen line signal |
| Helical antenna | HackRF SMA | RF TX | Radiates EM signal |
| PCM5102A DAC | Pi GPIO (I2S) | Mechanical | Converts digital → analogue |
| TPA3116D2 amp | DAC output | Mechanical | Amplifies signal for shaker |
| Bass shaker | Amp output | Mechanical | Converts electrical → vibration |
| Ground plate | Shaker mount | Mechanical | Transfers vibration to earth |
| Ground spike | Plate underside | Mechanical | Couples to soil |
| RTL-SDR v4 | Pi USB 2.0 | Monitor | Receives EM for analysis |
| Discone antenna | RTL-SDR SMA | Monitor | Wideband EM reception |
| USB magnetometer | Pi USB | Monitor | Magnetic field anomalies |
| Pi Camera | Pi CSI | Monitor | Sky observation |

---

## 2. Bill of Materials

### Tier 1: Mechanical Only (~£150)

No RF, no licence needed. Ground transduction only.

| # | Item | Model / Spec | Where to Buy | Est. Cost |
|---|------|-------------|--------------|-----------|
| 1 | Raspberry Pi 5 (4GB) | Broadcom BCM2712, 4GB RAM | The Pi Hut / Pimoroni | £50 |
| 2 | Pi 5 power supply | USB-C 27W (5V/5A) | The Pi Hut | £12 |
| 3 | MicroSD card | 32GB+ Class 10 / A2 | Amazon | £8 |
| 4 | I2S DAC board | PCM5102A breakout | Amazon / AliExpress | £8 |
| 5 | Class D amplifier | TPA3116D2 2-channel 50W | Amazon | £12 |
| 6 | 12V power supply | 12V 3A DC adapter (for amp) | Amazon | £8 |
| 7 | Bass shaker | Dayton Audio BST-1 (10W) | Parts Express / Amazon | £25 |
| 8 | Ground plate | 400mm aluminium disc, 6mm thick | eBay / metals4U | £20 |
| 9 | Ground spike | 300mm steel rod, 12mm dia | Screwfix / hardware store | £5 |
| 10 | Speaker wire | 14 AWG, 5m | Amazon | £6 |
| 11 | Jumper wires | Female-to-female dupont, 20cm | Amazon | £3 |
| 12 | M4 bolts + nuts | For mounting shaker to plate | Screwfix | £3 |
| | | | **Total** | **~£160** |

### Tier 2: Full Build (~£530)

Everything above, plus RF and monitoring.

| # | Item | Model / Spec | Where to Buy | Est. Cost |
|---|------|-------------|--------------|-----------|
| 13 | HackRF One | Great Scott Gadgets, 1 MHz–6 GHz | Lab401 / Amazon | £250 |
| 14 | Helical antenna | 1.42 GHz RHCP, SMA | eBay / build your own | £40 |
| 15 | SMA cable (TX) | SMA male–male, 1m, RG316 | Amazon | £8 |
| 16 | RTL-SDR v4 | RTL2832U + R828D, SMA | rtl-sdr.com | £30 |
| 17 | Discone antenna | 25 MHz–1.3 GHz wideband | Amazon / Moonraker | £40 |
| 18 | SMA cable (RX) | SMA male–male, 1m, RG316 | Amazon | £8 |
| 19 | USB magnetometer | RM3100 or HMC5883L breakout | Amazon / AliExpress | £15 |
| 20 | Pi Camera Module 3 | 12MP, autofocus, wide | The Pi Hut | £30 |
| | | | **Tier 2 additions** | **~£421** |
| | | | **Full total** | **~£530** |

### Tier 3: Field Portable (~£600)

Everything above, plus battery power and case.

| # | Item | Model / Spec | Where to Buy | Est. Cost |
|---|------|-------------|--------------|-----------|
| 21 | 12V LiFePO4 battery | 6Ah+ (powers amp + Pi via converter) | Amazon | £40 |
| 22 | 12V→5V USB-C converter | Buck converter for Pi | Amazon | £8 |
| 23 | Pelican-style case | IP67 waterproof, ~400×300×150mm | Amazon / Screwfix | £30 |
| 24 | Cable glands | PG9/PG11, waterproof feed-through | Amazon | £5 |
| | | | **Field additions** | **~£83** |
| | | | **Grand total** | **~£613** |

---

## 3. Tier 1: Mechanical Only Build

This is the simplest build. No RF, no licence, no SDR.

### What You Get

- Schumann resonance frequencies (7.83–33.8 Hz) coupled directly into the ground
- Prime-number pulse timing
- Multiple signal programmes
- Full protocol logging

### Signal Path

```
Pi 5 GPIO (I2S) → PCM5102A DAC → TPA3116D2 Amp → Bass Shaker → Ground Plate → Earth
```

---

## 4. Tier 2: Full Build

Adds RF transmission, EM monitoring, and anomaly detection.

### What You Get

Everything in Tier 1, plus:
- 1.42 GHz hydrogen line transmission (or ISM-legal 433/868 MHz)
- Schumann AM modulation on RF carrier
- Wideband EM monitoring with anomaly detection
- Magnetic field monitoring
- Sky camera
- Call-and-response protocol with automatic adaptation

---

## 5. Raspberry Pi 5 Setup

### 5.1 Flash the OS

1. Download **Raspberry Pi Imager** from raspberrypi.com
2. Insert microSD card into your computer
3. Select **Raspberry Pi OS (64-bit, Bookworm)**
4. Click the gear icon and configure:
   - Hostname: `hlb`
   - Enable SSH (password or key)
   - Set username: `pi`
   - Set password
   - Configure WiFi (your network SSID + password)
5. Write to SD card
6. Insert SD into Pi 5, connect power

### 5.2 First Boot

```bash
# SSH in
ssh pi@hlb.local
# or
ssh pi@<ip-address>

# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y \
    python3-pip \
    python3-numpy \
    python3-scipy \
    git \
    alsa-utils \
    libportaudio2

# Enable I2S (for DAC)
sudo raspi-config
# → Interface Options → I2S → Enable
# Reboot when prompted
```

### 5.3 Enable I2S Audio Output

Edit the boot config:

```bash
sudo nano /boot/firmware/config.txt
```

Add these lines at the end:

```
# I2S DAC output
dtoverlay=hifiberry-dac
dtoverlay=i2s-mmap
```

Edit ALSA config to use the DAC:

```bash
sudo nano /etc/asound.conf
```

Add:

```
pcm.!default {
    type hw
    card 0
}

ctl.!default {
    type hw
    card 0
}
```

Reboot:

```bash
sudo reboot
```

Verify the DAC appears:

```bash
aplay -l
# Should show the I2S/HiFiBerry device
```

---

## 6. Software Installation

### 6.1 Clone the Repository

```bash
cd ~
git clone https://github.com/DarrenEdwards111/UAP_Dog_Whistle.git
cd UAP_Dog_Whistle/hydrogen-line-beacon
```

### 6.2 Install the Package

```bash
pip3 install -e . --break-system-packages
```

### 6.3 Verify Installation

```bash
hlb --check
```

Expected output (Tier 1):
```
Hardware check:
  HackRF One:  ✗ Not found
  RTL-SDR:     ✗ Not found
  Audio (aplay): ✓ Available
```

### 6.4 Install HackRF Tools (Tier 2 only)

```bash
sudo apt install -y hackrf libhackrf-dev

# Verify
hackrf_info
# Should show "Found HackRF" with serial number
```

### 6.5 Install RTL-SDR Tools (Tier 2 only)

```bash
sudo apt install -y rtl-sdr librtlsdr-dev

# Blacklist default DVB-T driver (conflicts with SDR use)
echo "blacklist dvb_usb_rtl28xxu" | sudo tee /etc/modprobe.d/blacklist-rtl.conf
sudo modprobe -r dvb_usb_rtl28xxu

# Verify
rtl_test -t
# Should show "Found 1 device(s)"
```

---

## 7. Channel 1: Mechanical Assembly

### 7.1 Wiring the DAC

The PCM5102A connects to the Pi 5's GPIO header via I2S:

```
PCM5102A Board          Raspberry Pi 5 GPIO
──────────────          ───────────────────
VIN  ────────────────── Pin 1  (3.3V)
GND  ────────────────── Pin 6  (GND)
BCK  ────────────────── Pin 12 (GPIO 18 — I2S BCLK)
LCK  ────────────────── Pin 35 (GPIO 19 — I2S LRCLK)
DIN  ────────────────── Pin 40 (GPIO 21 — I2S DOUT)
```

Some PCM5102A boards also have:
```
FLT  ────────────────── GND (normal filter)
DMP  ────────────────── GND (de-emphasis off)
FMT  ────────────────── GND (I2S format)
SCL  ────────────────── Leave unconnected (or GND)
XMT  ────────────────── 3.3V (unmute)
```

### 7.2 Wiring the Amplifier

```
PCM5102A                TPA3116D2 Amplifier
────────                ───────────────────
L OUT ───────────────── L IN
GND   ───────────────── GND

12V DC Supply           TPA3116D2 Amplifier
─────────────           ───────────────────
+12V  ───────────────── VCC / V+
GND   ───────────────── GND

TPA3116D2 Amplifier     Bass Shaker
───────────────────     ───────────
L OUT+ ──────────────── + (red)
L OUT- ──────────────── - (black)
```

**Important:** The amplifier runs on 12V DC, NOT from the Pi's 5V. Use a separate 12V power supply or 12V battery.

### 7.3 Assembling the Ground Coupler

```
        ┌─────────────────────┐
        │    Bass Shaker      │
        │   (Dayton BST-1)    │
        │                     │
        │  ┌───┐   ┌───┐     │
        │  │M4 │   │M4 │     │  ← 4x M4 bolts through
        │  │bolt│   │bolt│     │     shaker mounting holes
        │  └─┬─┘   └─┬─┘     │
        └────┼───────┼───────┘
             │       │
        ┌────▼───────▼───────┐
        │                     │
        │   Aluminium Plate   │  ← 400mm diameter, 6mm thick
        │   (ground plate)    │     Drill 4x M4 holes to match shaker
        │                     │
        └──────────┬──────────┘
                   │
              ┌────▼────┐
              │ Ground  │  ← 300mm steel rod, 12mm diameter
              │  Spike  │     Welded or bolted to centre of plate
              │         │     Drives into soil
              └─────────┘
```

**Assembly steps:**

1. **Drill mounting holes** in the aluminium plate to match the bass shaker's bolt pattern (usually 4 holes in a square)
2. **Bolt the shaker** to the centre of the plate using M4 bolts, washers, and lock nuts. Tighten firmly — vibration will loosen anything that isn't locked.
3. **Attach the ground spike** to the underside of the plate:
   - **Option A (best):** Weld the steel rod perpendicular to the plate centre
   - **Option B:** Drill a 12mm hole through the plate, push the rod through, secure with nuts on both sides
   - **Option C:** Use a heavy-duty U-bolt to clamp the rod to the plate underside
4. **Connect speaker wire** from the amplifier to the shaker terminals

### 7.4 Testing the Mechanical Channel

```bash
# Generate a 10-second test file
hlb --generate /tmp/test.wav --duration 10 --programme fundamental

# Play it
aplay /tmp/test.wav

# You should feel 7.83 Hz vibration through the plate
# It won't be audible — it's below human hearing
# Place your hand on the plate to feel it
```

---

## 8. Channel 2: RF Assembly

### 8.1 HackRF One Connection

Simple — USB cable:

```
Raspberry Pi 5          HackRF One
──────────────          ──────────
USB 3.0 port ────────── USB-C port (use the blue USB port on Pi for best throughput)
```

### 8.2 Helical Antenna for 1.42 GHz

A circularly polarised helical antenna is ideal for hydrogen line work. You can buy one or build one.

**DIY Helical Antenna (1.42 GHz, RHCP):**

```
Materials:
  - 2mm copper wire, ~2m length
  - PVC pipe, 67mm diameter, 300mm long
  - SMA female chassis connector
  - Ground plane: 150mm × 150mm aluminium sheet
  - 4mm wooden dowel (winding guide)

Dimensions (for 1.42 GHz):
  Circumference:    C = λ = 211mm (wire wound around 67mm PVC pipe)
  Spacing:          S = λ/4 = 53mm between turns
  Number of turns:  N = 6 (gives ~12 dBi gain)
  Total height:     H = N × S = 318mm
  Wire length:      L = N × C = 1,266mm
  Ground plane:     ≥ 0.75λ × 0.75λ = 158mm × 158mm

Build:
  1. Mark 6 equally spaced lines on the PVC pipe (53mm apart)
  2. Wind the copper wire around the pipe following the marks
     — wind RIGHT-HAND (clockwise when viewed from feed end) for RHCP
  3. Solder the bottom end of the wire to the SMA connector centre pin
  4. Mount the SMA connector through the ground plane
  5. Solder ground plane to SMA connector ground
```

```
        ↑ Direction of radiation
        │
    ╭───┼───╮
    │ ╭─┼─╮ │   ← Turn 6 (top)
    │ │ │ │ │
    │ ╭─┼─╮ │   ← Turn 5
    │ │ │ │ │
    │ ╭─┼─╮ │   ← Turn 4
    │ │ │ │ │        53mm spacing
    │ ╭─┼─╮ │   ← Turn 3
    │ │ │ │ │
    │ ╭─┼─╮ │   ← Turn 2
    │ │ │ │ │
    │ ╰─┼─╯ │   ← Turn 1 (feed)
    │   │   │
    ╰───┼───╯
   ┌────┼────────┐
   │    ●        │  ← SMA connector (centre pin to wire)
   │  Ground     │  ← 150mm × 150mm aluminium
   │  Plane      │
   └─────────────┘
```

**Or buy:** Search eBay/Amazon for "1420 MHz helical antenna" or "hydrogen line antenna" — radio astronomy hobbyists sell these for £30–60.

### 8.3 SMA Connections

```
HackRF One (SMA female) ──── SMA cable (male-male, 1m) ──── Antenna (SMA female)
```

Use RG316 or RG58 cable. Keep it short — every metre of cable loses ~0.5 dB at 1.4 GHz.

### 8.4 Testing the RF Channel

```bash
# Generate a 10-second baseband file
hlb --generate-rf /tmp/test.iq

# Verify HackRF
hackrf_info

# Test transmit (433 MHz ISM — legal, safe)
hackrf_transfer -t /tmp/test.iq -f 433920000 -s 2000000 -x 10

# Stop with Ctrl+C
```

**⚠️ Do not transmit on 1.42 GHz without a ham licence. Use 433 MHz for testing.**

---

## 9. Monitoring Station Assembly

### 9.1 RTL-SDR Receiver

```
Raspberry Pi 5          RTL-SDR v4
──────────────          ──────────
USB 2.0 port ────────── USB-A connector

RTL-SDR v4 (SMA)        Discone Antenna
─────────────────        ───────────────
SMA female ───────────── SMA cable ───── Antenna base
```

The discone antenna should be mounted as high as possible — ideally on a tripod or mast, minimum 2m above ground.

### 9.2 USB Magnetometer (Optional)

```
Raspberry Pi 5          RM3100 / HMC5883L
──────────────          ──────────────────
USB port     ────────── USB breakout board
```

Or via I2C if using a bare breakout:
```
RM3100 Board            Raspberry Pi 5 GPIO
────────────            ───────────────────
VIN  ────────────────── Pin 17 (3.3V)
GND  ────────────────── Pin 9  (GND)
SDA  ────────────────── Pin 3  (GPIO 2 — I2C SDA)
SCL  ────────────────── Pin 5  (GPIO 3 — I2C SCL)
```

### 9.3 Pi Camera (Optional)

```
Pi Camera Module 3 (ribbon cable) → Pi 5 CSI connector
```

1. Lift the CSI connector latch on the Pi
2. Insert the ribbon cable (contacts facing the board)
3. Press the latch down

Test:
```bash
rpicam-still -o test.jpg
```

---

## 10. Field Deployment

### 10.1 Site Selection

**Ideal characteristics:**
- Remote — minimal RF interference (away from cities, cell towers, WiFi)
- Open sky — unobstructed view, no overhead powerlines
- Soil ground — for spike coupling (not concrete/tarmac)
- Dark — for visual observation (no light pollution)
- Legal access — private land with permission, or public land where permitted

**UK suggestions:**
- Brecon Beacons (dark sky reserve)
- Gower Peninsula (Darren — this is right on your doorstep)
- Snowdonia
- Scottish Highlands
- Any rural area away from major roads

### 10.2 Setup Procedure

```
Time: Allow 30 minutes for full setup

1. CHOOSE LOCATION
   - Flat ground, away from trees and structures
   - Good soil for ground spike (not rocky)

2. DEPLOY GROUND COUPLER
   - Drive ground spike into soil (hammer it in ~200mm)
   - Ensure plate sits flat and firm
   - Run speaker wire to amplifier location (2-5m)

3. SET UP ELECTRONICS
   - Place Pi, amp, and battery in case (or on dry surface)
   - Connect: DAC → Amp → Speaker wire → Shaker
   - Connect: 12V battery → Amp
   - Connect: 5V supply → Pi

4. DEPLOY ANTENNAS (Tier 2)
   - TX antenna: mount on tripod, point upward (or at target sky area)
   - RX antenna: mount on separate tripod, 5m+ from TX antenna
   - Connect SMA cables to HackRF and RTL-SDR
   - Ensure antennas are >2m from people during operation

5. POWER ON
   - Boot Pi (takes ~30 seconds)
   - SSH in: ssh pi@hlb.local

6. CAPTURE BASELINE (Tier 2)
   - Run: hlb --baseline
   - Wait 2-3 minutes for baseline capture
   - This establishes "normal" EM environment

7. START PROTOCOL
   - Tier 1: hlb --duration 3600
   - Tier 2: hlb --rf --freq 433 --duration 3600
   - Full:   hlb --rf --freq hydrogen --duration 3600
```

### 10.3 Field Layout

```
                    N
                    ↑
                    │
           ┌───────┼───────┐
           │   TX Antenna   │  ← On tripod, 2m high
           │   (Helical)    │    Pointed at sky
           └───────┬───────┘
                   │ SMA cable (1m)
                   │
    ┌──────────────┼──────────────┐
    │         EQUIPMENT           │
    │  ┌─────┐ ┌──────┐ ┌─────┐  │
    │  │Pi 5 │ │Amp   │ │Batt │  │
    │  │     │ │12V   │ │12V  │  │  ← In weatherproof case
    │  │HackRF │TPA3116│ │LiFe │  │    or under tarp
    │  │RTL-SDR│      │ │PO4  │  │
    │  └──┬──┘ └──┬───┘ └─────┘  │
    │     │       │               │
    └─────┼───────┼───────────────┘
          │       │
          │       │ Speaker wire (3-5m)
          │       │
          │  ┌────▼─────┐
          │  │  Ground   │  ← Centre of deployment area
          │  │  Plate +  │    Spike driven into soil
          │  │  Shaker   │
          │  └───────────┘
          │
          │ SMA cable (5m)
          │
    ┌─────▼─────┐
    │ RX Antenna │  ← On separate tripod, 5m+ from TX
    │ (Discone)  │    2m+ high
    └───────────┘


    OBSERVER: 10m+ from equipment
    ┌─────────┐
    │  You    │  ← Laptop with SSH, or just let it run
    │  (here) │    Bring chair, thermos, binoculars, camera
    └─────────┘
```

---

## 11. Operating Procedures

### 11.1 Standard Session

```bash
# SSH into Pi
ssh pi@hlb.local

# Quick check
hlb --check

# Start (1 hour, mechanical only)
hlb --duration 3600

# Start (1 hour, full protocol, 433 MHz ISM legal)
hlb --rf --freq 433 --duration 3600

# Start (1 hour, full protocol, hydrogen line — REQUIRES HAM LICENCE)
hlb --rf --freq hydrogen --duration 3600
```

### 11.2 Automated Session (systemd)

For unattended operation:

```bash
# Create service file
sudo tee /etc/systemd/system/hlb.service << 'EOF'
[Unit]
Description=Hydrogen Line Beacon
After=network.target sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/home/pi/.local/bin/hlb --duration 7200 --programme full
Restart=on-failure
RestartSec=30
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable hlb.service
sudo systemctl start hlb.service

# Check status
sudo systemctl status hlb.service

# View logs
journalctl -u hlb.service -f
```

### 11.3 Reading the Logs

All events are logged to `./hlb_logs/`:

```bash
# Session summary
cat hlb_logs/session_*.json | python3 -m json.tool

# Event log (today)
cat hlb_logs/events_$(date +%Y%m%d).jsonl

# Count anomalies
grep '"type": "anomaly"' hlb_logs/events_*.jsonl | wc -l
```

### 11.4 What to Record Manually

Keep a field notebook (or phone notes) with:
- Date, time, location (GPS coordinates)
- Weather conditions (clear, cloudy, temperature, wind)
- Moon phase
- Programme used and duration
- Any visual observations (lights, movement, anything unusual)
- Any sounds or sensations
- Any equipment anomalies (unexpected readings, interference)
- Timestamps of anything interesting

---

## 12. Troubleshooting

### No sound from shaker

```bash
# Check audio output
aplay -l
# Should list the I2S DAC

# Test with a tone
speaker-test -t sine -f 100 -l 1
# 100 Hz is audible — if the shaker vibrates, wiring is correct

# Check I2S is enabled
cat /boot/firmware/config.txt | grep hifiberry
# Should show: dtoverlay=hifiberry-dac
```

### HackRF not detected

```bash
# Check USB
lsusb | grep -i hackrf
# Should show: "Great Scott Gadgets HackRF One"

# Check firmware
hackrf_info
# If error: try different USB cable or port

# Permissions
sudo usermod -aG plugdev pi
# Then log out and back in
```

### RTL-SDR not detected

```bash
# Check USB
lsusb | grep -i rtl
# Should show: "Realtek Semiconductor Corp. RTL2838"

# Check driver blacklist
cat /etc/modprobe.d/blacklist-rtl.conf
# Should show: blacklist dvb_usb_rtl28xxu

# If the DVB driver loaded first:
sudo modprobe -r dvb_usb_rtl28xxu
sudo modprobe rtl2832_sdr
```

### Low signal / weak vibration

- **Check amplifier gain** — turn the potentiometer on the TPA3116D2
- **Check 12V supply** — amp needs real 12V, not 5V from Pi
- **Check shaker mounting** — must be bolted tight to plate, not just resting
- **Check ground spike** — must be driven into real soil, not sitting on surface
- **Check speaker wire** — 14 AWG minimum, no breaks, good connections

### Protocol shows no anomalies

- This is normal — anomalies are rare events
- Verify baseline was captured (check `hlb_logs/baseline.json`)
- Try lowering threshold: edit config to `anomaly_threshold: 2.0`
- Ensure RX antenna is not too close to TX antenna (>5m separation)
- Check RTL-SDR is actually receiving (run `rtl_power` manually)

---

## 13. Safety

### RF Exposure

- Keep all people **>2m from the TX antenna** during transmission
- At 100 mW output, this distance provides a large safety margin
- The HackRF One's maximum output is 15 dBm (~30 mW) which is well within safe limits
- ISM band power limits are set specifically to be safe for incidental exposure

### Electrical

- The 12V amplifier circuit is low voltage and safe to touch
- Do not expose electronics to rain — use a waterproof case or cover
- Disconnect battery before modifying any wiring
- Use appropriate fuses on the 12V circuit (3A)

### Infrasound

- The mechanical channel produces sub-20 Hz vibrations
- At the power levels used (10–50W shaker), these are well below harmful thresholds
- You may feel a mild tingling or vibration standing near the plate — this is normal
- Harmful infrasound levels (>120 dB) require industrial equipment far beyond this build

### Lightning

- **Do not operate during thunderstorms** — the antennas are lightning attractors
- Take down antennas if storms are approaching
- Do not deploy on hilltops during unsettled weather

### UAP-Specific (per Skywatcher's Warnings)

- Skywatcher personnel report **historic injuries** from close UAP encounters including radiation exposure and directed energy
- If anything anomalous appears **at close range**, do not approach
- Consider bringing a **dosimeter** (radiation badge) — available for ~£20 on Amazon
- Maintain minimum **50m distance** from any observed anomaly
- Have a vehicle nearby for rapid departure if needed
- Tell someone where you are and when you'll be back

### Legal

- **433 MHz / 868 MHz:** Legal in UK/EU without licence at specified power levels
- **1.42 GHz:** Requires amateur radio licence (Foundation minimum — £50, one day)
- **Run `hlb --legal` for full details**
- You are responsible for compliance with Ofcom regulations

---

*Mikoshi Ltd, 2026 — MIT Licence*

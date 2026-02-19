# Raspberry Pi Setup Guide

## Hardware
- Raspberry Pi (any model, Pi 4/5 recommended)
- Bluetooth speaker (or wired speaker/3.5mm)
- Optional: PiSugar battery for portable use

## Install Dependencies
```bash
sudo apt-get update
sudo apt-get install -y python3-pip libportaudio2
pip3 install numpy scipy
```

## Quick Start (Manual)
```bash
# Generate 1-hour WAV file (~300MB, takes 1-2 min on Pi 4)
python3 uap3-generator.py --duration 3600

# Play it
aplay uap3_output.wav
```

## Auto-Start on Boot (systemd)
```bash
# Copy files to home directory
cp uap3-generator.py ~/
cp uap3-player.py ~/

# Install the service
sudo cp uap3-player.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable uap3-player.service
sudo systemctl start uap3-player.service
```

## Bluetooth Speaker Setup
```bash
bluetoothctl
scan on
# Wait for your speaker to appear, note the MAC address
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
exit
```

## Check Status
```bash
sudo systemctl status uap3-player.service
cat ~/uap3-player.log
```

## Custom Duration
```bash
# 30 minutes
python3 uap3-generator.py --duration 1800

# 2 hours
python3 uap3-generator.py --duration 7200
```

## Signal Layers
1. **Schumann Resonance** (7.83 Hz) — AM modulated over 100 Hz carrier
2. **Harmonic Tone** (528 Hz) — with harmonics at 1056, 1584, 2112 Hz
3. **High-Frequency Pings** (17 kHz) — every 5 seconds
4. **Frequency Chirps** (2.5→4 kHz) — sweep every 10 seconds
5. **Ambient Pad** (432 Hz) — with harmonics at 864, 1296, 2160 Hz
6. **Breathing White Noise** — 0.25 Hz breathing cycle

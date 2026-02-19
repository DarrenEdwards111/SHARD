#!/usr/bin/env python3
"""
UAP Dog Whistle Player Service
Monitors for the WAV file and plays it on loop via the default audio output.
Designed to run as a systemd service on Raspberry Pi.
"""

import subprocess
import time
import os
import sys

WAV_FILE = os.path.expanduser("~/uap3_output.wav")
GENERATOR = os.path.expanduser("~/uap3-generator.py")
LOG_FILE = os.path.expanduser("~/uap3-player.log")


def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def generate_if_missing():
    if not os.path.exists(WAV_FILE):
        log(f"WAV file not found at {WAV_FILE}, generating...")
        try:
            subprocess.run(
                [sys.executable, GENERATOR, "--duration", "3600", "--output", WAV_FILE],
                check=True, timeout=600
            )
            log("WAV file generated successfully.")
        except Exception as e:
            log(f"Error generating WAV: {e}")
            return False
    return True


def play_loop():
    log("Starting playback loop...")
    while True:
        try:
            log("Playing uap3_output.wav...")
            result = subprocess.run(
                ["aplay", WAV_FILE],
                timeout=7200  # 2 hour timeout (safety)
            )
            if result.returncode != 0:
                log(f"aplay exited with code {result.returncode}")
                time.sleep(5)
        except subprocess.TimeoutExpired:
            log("Playback timeout, restarting...")
        except KeyboardInterrupt:
            log("Stopped by user.")
            break
        except Exception as e:
            log(f"Playback error: {e}")
            time.sleep(10)


def main():
    log("UAP Dog Whistle Player starting...")

    if not generate_if_missing():
        log("Cannot start without WAV file. Exiting.")
        sys.exit(1)

    play_loop()


if __name__ == "__main__":
    main()

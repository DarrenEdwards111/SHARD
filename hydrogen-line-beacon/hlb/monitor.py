"""
Monitor — Passive listening and anomaly detection.
Uses RTL-SDR or HackRF in receive mode to monitor for responses.
"""

import numpy as np
import subprocess
import threading
import time
import json
import os
from datetime import datetime
from .constants import HYDROGEN_LINE_HZ, WATER_HOLE_LOW, WATER_HOLE_HIGH


class Monitor:
    """
    Passive monitoring for EM responses and anomalies.
    
    Capabilities:
        - Wideband spectrum monitoring via RTL-SDR
        - Power level logging at specific frequencies
        - Anomaly detection (significant deviations from baseline)
        - JSON event logging with timestamps
    
    Signal path: Antenna → RTL-SDR (USB) → Pi → Analysis
    """
    
    def __init__(self, log_dir="./hlb_logs"):
        self.log_dir = log_dir
        self.baseline = None
        self.running = False
        self._thread = None
        os.makedirs(log_dir, exist_ok=True)
    
    @staticmethod
    def is_available():
        """Check if RTL-SDR tools are installed."""
        try:
            result = subprocess.run(
                ["rtl_test", "-t"], capture_output=True, text=True, timeout=5
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def power_scan(self, freq_start=None, freq_end=None, bin_size=1000):
        """
        Single power spectrum scan using rtl_power.
        
        Returns dict of {frequency_hz: power_db}.
        """
        if freq_start is None:
            freq_start = int(WATER_HOLE_LOW)
        if freq_end is None:
            freq_end = int(WATER_HOLE_HIGH)
        
        outfile = os.path.join(self.log_dir, "scan_tmp.csv")
        
        try:
            subprocess.run([
                "rtl_power",
                "-f", f"{freq_start}:{freq_end}:{bin_size}",
                "-1",  # single scan
                "-g", "40",
                outfile
            ], capture_output=True, timeout=30)
            
            return self._parse_power_csv(outfile)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return {}
    
    def _parse_power_csv(self, filename):
        """Parse rtl_power CSV output into frequency:power dict."""
        results = {}
        try:
            with open(filename, 'r') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) < 7:
                        continue
                    freq_start = float(parts[2])
                    freq_step = float(parts[4])
                    powers = [float(p) for p in parts[6:] if p.strip()]
                    for i, power in enumerate(powers):
                        freq = freq_start + i * freq_step
                        results[freq] = power
        except (IOError, ValueError):
            pass
        return results
    
    def capture_baseline(self, samples=5):
        """
        Capture baseline power spectrum (average of multiple scans).
        Run this BEFORE transmitting to establish normal conditions.
        """
        print(f"  Capturing baseline ({samples} samples)...")
        all_scans = []
        for i in range(samples):
            scan = self.power_scan()
            if scan:
                all_scans.append(scan)
            time.sleep(2)
        
        if not all_scans:
            print("  Warning: No baseline data captured (is RTL-SDR connected?)")
            return
        
        # Average power at each frequency
        all_freqs = set()
        for scan in all_scans:
            all_freqs.update(scan.keys())
        
        self.baseline = {}
        for freq in all_freqs:
            powers = [s.get(freq, -100) for s in all_scans if freq in s]
            self.baseline[freq] = {
                'mean': np.mean(powers),
                'std': np.std(powers),
            }
        
        # Save baseline
        baseline_file = os.path.join(self.log_dir, "baseline.json")
        with open(baseline_file, 'w') as f:
            json.dump({str(k): v for k, v in self.baseline.items()}, f)
        
        print(f"  Baseline captured: {len(self.baseline)} frequency bins")
    
    def detect_anomalies(self, threshold_sigma=3.0):
        """
        Compare current scan to baseline.
        Returns list of anomalous frequencies with details.
        """
        if self.baseline is None:
            return []
        
        current = self.power_scan()
        anomalies = []
        
        for freq, power in current.items():
            if freq in self.baseline:
                bl = self.baseline[freq]
                if bl['std'] > 0:
                    sigma = (power - bl['mean']) / bl['std']
                    if abs(sigma) > threshold_sigma:
                        anomalies.append({
                            'frequency_hz': freq,
                            'power_db': power,
                            'baseline_mean': bl['mean'],
                            'baseline_std': bl['std'],
                            'sigma': sigma,
                            'timestamp': datetime.utcnow().isoformat(),
                        })
        
        return anomalies
    
    def log_event(self, event_type, data):
        """Log an event to the JSON event log."""
        event = {
            'type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data,
        }
        
        log_file = os.path.join(
            self.log_dir,
            f"events_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        )
        with open(log_file, 'a') as f:
            f.write(json.dumps(event) + '\n')
        
        return event
    
    def start_continuous(self, interval=30, threshold_sigma=3.0):
        """
        Start continuous monitoring in background thread.
        Logs anomalies automatically.
        """
        self.running = True
        
        def _monitor_loop():
            while self.running:
                anomalies = self.detect_anomalies(threshold_sigma)
                if anomalies:
                    for a in anomalies:
                        self.log_event('anomaly', a)
                        print(f"  ⚠ ANOMALY: {a['frequency_hz']/1e6:.3f} MHz, "
                              f"{a['sigma']:.1f}σ above baseline")
                time.sleep(interval)
        
        self._thread = threading.Thread(target=_monitor_loop, daemon=True)
        self._thread.start()
    
    def stop_continuous(self):
        """Stop continuous monitoring."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
    
    def get_events(self, date=None):
        """Read events from log file."""
        if date is None:
            date = datetime.utcnow().strftime('%Y%m%d')
        
        log_file = os.path.join(self.log_dir, f"events_{date}.jsonl")
        events = []
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    events.append(json.loads(line))
        except IOError:
            pass
        return events

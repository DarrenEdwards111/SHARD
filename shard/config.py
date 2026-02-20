"""
Configuration for Active Protocol Discovery integration with HLB.

Defines parameters for SPRT sequential testing, probe transmission,
response analysis, and hardware settings.
"""

from dataclasses import dataclass, field
from typing import Dict, Any
import sys
import os

# Add hydrogen-line-beacon to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../hydrogen-line-beacon'))
from hlb.constants import HYDROGEN_LINE_HZ, RF_SAMPLE_RATE, RF_DEFAULT_GAIN


@dataclass
class APDConfig:
    """Configuration for Active Protocol Discovery session.
    
    Attributes
    ----------
    sprt_alpha : float
        Type I error rate (false positive: detecting adaptive response when none exists).
    sprt_beta : float
        Type II error rate (false negative: missing adaptive response).
    max_iterations : int
        Maximum number of probe-response cycles before timeout.
    probe_duration : float
        Duration of each probe transmission in seconds.
    listen_duration : float
        Duration of listen window after probe in seconds.
    inter_probe_delay : float
        Silence interval between probes in seconds (baseline observation).
    carrier_freq : float
        RF carrier frequency in Hz (default: 1420.405 MHz hydrogen line).
    sample_rate : int
        SDR sample rate in Hz.
    tx_gain : int
        Transmission gain in dB.
    rx_gain : int
        Reception gain in dB for monitoring.
    bandwidth : int
        Receiver bandwidth in Hz.
    center_freq_offset : float
        Frequency offset from carrier for monitoring (Hz).
    anomaly_threshold_sigma : float
        Number of standard deviations above baseline for anomaly detection.
    log_dir : str
        Directory for session logs and data.
    probe_library_seed : int or None
        Random seed for probe generation (None = non-deterministic).
    """
    
    # SPRT parameters
    sprt_alpha: float = 0.01
    sprt_beta: float = 0.01
    
    # Session control
    max_iterations: int = 100
    
    # Timing parameters
    probe_duration: float = 5.0
    listen_duration: float = 15.0
    inter_probe_delay: float = 10.0
    
    # RF parameters
    carrier_freq: float = HYDROGEN_LINE_HZ
    sample_rate: int = RF_SAMPLE_RATE
    tx_gain: int = RF_DEFAULT_GAIN
    rx_gain: int = 40
    bandwidth: int = 2_000_000
    center_freq_offset: float = 0.0
    
    # Analysis parameters
    anomaly_threshold_sigma: float = 3.0
    baseline_samples: int = 5
    noise_floor_percentile: float = 25.0
    
    # Paths
    log_dir: str = "./apd_logs"
    temp_dir: str = "/tmp/apd_active"
    
    # Probe library
    probe_library_seed: int | None = None
    probe_types: list = field(default_factory=lambda: [
        "hydrogen_pulse",
        "schumann_am",
        "frequency_sweep",
        "prime_sequence",
        "fibonacci_sequence",
        "silence"
    ])
    
    # Safety limits
    legal_check: bool = True
    require_ham_license_confirm: bool = True
    
    def validate(self):
        """Validate configuration parameters."""
        if not (0 < self.sprt_alpha < 1):
            raise ValueError(f"sprt_alpha must be in (0,1), got {self.sprt_alpha}")
        if not (0 < self.sprt_beta < 1):
            raise ValueError(f"sprt_beta must be in (0,1), got {self.sprt_beta}")
        if self.max_iterations < 1:
            raise ValueError(f"max_iterations must be positive, got {self.max_iterations}")
        if self.probe_duration <= 0:
            raise ValueError(f"probe_duration must be positive, got {self.probe_duration}")
        if self.listen_duration <= 0:
            raise ValueError(f"listen_duration must be positive, got {self.listen_duration}")
        
        # Legal frequency check
        if self.legal_check and abs(self.carrier_freq - HYDROGEN_LINE_HZ) < 1e6:
            if self.require_ham_license_confirm:
                print("⚠️  WARNING: Operating on 1420 MHz hydrogen line requires amateur radio licence.")
                print("   UK: Foundation licence minimum (one-day course, ~£50)")
                print("   Set require_ham_license_confirm=False to suppress this check.")
                raise RuntimeError("Unlicensed transmission on 1420 MHz is illegal in most jurisdictions.")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "sprt": {
                "alpha": self.sprt_alpha,
                "beta": self.sprt_beta,
            },
            "timing": {
                "probe_duration": self.probe_duration,
                "listen_duration": self.listen_duration,
                "inter_probe_delay": self.inter_probe_delay,
            },
            "rf": {
                "carrier_freq": self.carrier_freq,
                "sample_rate": self.sample_rate,
                "tx_gain": self.tx_gain,
                "rx_gain": self.rx_gain,
            },
            "analysis": {
                "anomaly_threshold_sigma": self.anomaly_threshold_sigma,
                "baseline_samples": self.baseline_samples,
            },
            "session": {
                "max_iterations": self.max_iterations,
                "log_dir": self.log_dir,
            }
        }

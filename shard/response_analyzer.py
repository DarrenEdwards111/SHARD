"""
Response Analyzer — Statistical analysis of RF responses to probes.

Processes captured IQ data to detect anomalies and compute metrics
for the APD sequential hypothesis test.
"""

import numpy as np
from scipy import signal, stats
from dataclasses import dataclass
from typing import Optional, Tuple
import logging


@dataclass
class ResponseMetrics:
    """Metrics computed from a response observation.
    
    Attributes
    ----------
    probe_id : int
        Index of the probe that generated this response.
    power_mean : float
        Mean power spectral density during listen window.
    power_std : float
        Standard deviation of power.
    snr_db : float
        Signal-to-noise ratio in dB.
    anomaly_score : float
        Statistical deviation from baseline (in sigma).
    correlation : float
        Cross-correlation with transmitted probe.
    peak_freq : float or None
        Frequency of peak response (Hz).
    peak_power : float
        Power at peak frequency.
    is_anomaly : bool
        True if anomaly_score exceeds threshold.
    raw_iq : np.ndarray or None
        Raw IQ samples (optional, for debugging).
    """
    probe_id: int
    power_mean: float
    power_std: float
    snr_db: float
    anomaly_score: float
    correlation: float
    peak_freq: Optional[float]
    peak_power: float
    is_anomaly: bool
    raw_iq: Optional[np.ndarray] = None
    
    def to_dict(self):
        """Convert to dictionary for logging."""
        return {
            "probe_id": self.probe_id,
            "power_mean": float(self.power_mean),
            "power_std": float(self.power_std),
            "snr_db": float(self.snr_db),
            "anomaly_score": float(self.anomaly_score),
            "correlation": float(self.correlation),
            "peak_freq": float(self.peak_freq) if self.peak_freq else None,
            "peak_power": float(self.peak_power),
            "is_anomaly": bool(self.is_anomaly),
        }


class ResponseAnalyzer:
    """Analyzes RF responses to detect anomalies and compute APD metrics.
    
    Parameters
    ----------
    sample_rate : int
        SDR sample rate in Hz.
    anomaly_threshold : float
        Number of standard deviations above baseline for anomaly detection.
    baseline_mean : float or None
        Pre-computed baseline power mean. If None, computed from baseline samples.
    baseline_std : float or None
        Pre-computed baseline power std. If None, computed from baseline samples.
    """
    
    def __init__(
        self,
        sample_rate: int = 2_000_000,
        anomaly_threshold: float = 3.0,
        baseline_mean: Optional[float] = None,
        baseline_std: Optional[float] = None,
    ):
        self.sr = sample_rate
        self.anomaly_threshold = anomaly_threshold
        self.baseline_mean = baseline_mean
        self.baseline_std = baseline_std
        self.logger = logging.getLogger(__name__)
    
    def set_baseline(self, iq_samples_list: list[np.ndarray]):
        """Compute baseline statistics from silence/pre-probe samples.
        
        Parameters
        ----------
        iq_samples_list : list of np.ndarray
            List of IQ sample arrays captured during silence.
        """
        power_samples = []
        for iq in iq_samples_list:
            power = self._compute_power_spectrum(iq)
            power_samples.append(np.mean(power))
        
        self.baseline_mean = np.mean(power_samples)
        self.baseline_std = np.std(power_samples)
        
        self.logger.info(
            f"Baseline computed: mean={self.baseline_mean:.3e}, "
            f"std={self.baseline_std:.3e}"
        )
    
    def analyze(
        self,
        probe_id: int,
        response_iq: np.ndarray,
        probe_iq: Optional[np.ndarray] = None,
        save_raw: bool = False,
    ) -> ResponseMetrics:
        """Analyze a response to a probe.
        
        Parameters
        ----------
        probe_id : int
            Index of the probe.
        response_iq : np.ndarray
            Captured IQ samples during listen window.
        probe_iq : np.ndarray or None
            Transmitted probe IQ (for correlation analysis).
        save_raw : bool
            If True, include raw IQ in metrics (for debugging).
        
        Returns
        -------
        ResponseMetrics
            Computed metrics.
        """
        # Power spectral density
        psd = self._compute_power_spectrum(response_iq)
        power_mean = np.mean(psd)
        power_std = np.std(psd)
        
        # Peak detection
        peak_freq, peak_power = self._find_peak(psd)
        
        # SNR estimation
        noise_floor = np.percentile(psd, 25)
        snr_linear = peak_power / (noise_floor + 1e-12)
        snr_db = 10 * np.log10(snr_linear) if snr_linear > 0 else -np.inf
        
        # Anomaly detection
        if self.baseline_mean is not None and self.baseline_std is not None:
            anomaly_score = (power_mean - self.baseline_mean) / (self.baseline_std + 1e-12)
            is_anomaly = anomaly_score > self.anomaly_threshold
        else:
            anomaly_score = 0.0
            is_anomaly = False
            self.logger.warning("No baseline set. Anomaly detection disabled.")
        
        # Cross-correlation with probe
        correlation = 0.0
        if probe_iq is not None:
            correlation = self._compute_correlation(response_iq, probe_iq)
        
        return ResponseMetrics(
            probe_id=probe_id,
            power_mean=power_mean,
            power_std=power_std,
            snr_db=snr_db,
            anomaly_score=anomaly_score,
            correlation=correlation,
            peak_freq=peak_freq,
            peak_power=peak_power,
            is_anomaly=is_anomaly,
            raw_iq=response_iq if save_raw else None,
        )
    
    def _compute_power_spectrum(self, iq_samples: np.ndarray) -> np.ndarray:
        """Compute power spectral density from IQ samples.
        
        Parameters
        ----------
        iq_samples : np.ndarray
            Interleaved IQ int8 samples or complex float.
        
        Returns
        -------
        np.ndarray
            Power spectral density (linear scale).
        """
        # Convert to complex if needed
        if iq_samples.dtype == np.int8:
            i = iq_samples[0::2].astype(float) / 127.0
            q = iq_samples[1::2].astype(float) / 127.0
            complex_signal = i + 1j * q
        else:
            complex_signal = iq_samples
        
        # Welch's method for PSD estimation
        freqs, psd = signal.welch(
            complex_signal,
            fs=self.sr,
            nperseg=min(1024, len(complex_signal)),
            scaling='density',
        )
        
        return psd
    
    def _find_peak(self, psd: np.ndarray) -> Tuple[Optional[float], float]:
        """Find the peak frequency and power in PSD.
        
        Returns
        -------
        peak_freq : float or None
            Frequency of peak in Hz.
        peak_power : float
            Power at peak.
        """
        peak_idx = np.argmax(psd)
        peak_power = psd[peak_idx]
        
        # Convert index to frequency
        n_freqs = len(psd)
        freq_bins = np.fft.fftfreq(n_freqs * 2, 1 / self.sr)[:n_freqs]
        peak_freq = freq_bins[peak_idx] if peak_idx < len(freq_bins) else None
        
        return peak_freq, peak_power
    
    def _compute_correlation(
        self, 
        response_iq: np.ndarray, 
        probe_iq: np.ndarray
    ) -> float:
        """Compute normalized cross-correlation between response and probe.
        
        Returns
        -------
        float
            Pearson correlation coefficient.
        """
        # Convert both to complex
        if response_iq.dtype == np.int8:
            i_r = response_iq[0::2].astype(float)
            q_r = response_iq[1::2].astype(float)
            response_complex = i_r + 1j * q_r
        else:
            response_complex = response_iq
        
        if probe_iq.dtype == np.int8:
            i_p = probe_iq[0::2].astype(float)
            q_p = probe_iq[1::2].astype(float)
            probe_complex = i_p + 1j * q_p
        else:
            probe_complex = probe_iq
        
        # Truncate to same length
        min_len = min(len(response_complex), len(probe_complex))
        response_complex = response_complex[:min_len]
        probe_complex = probe_complex[:min_len]
        
        # Pearson correlation of magnitudes
        response_mag = np.abs(response_complex)
        probe_mag = np.abs(probe_complex)
        
        if np.std(response_mag) < 1e-12 or np.std(probe_mag) < 1e-12:
            return 0.0
        
        correlation = np.corrcoef(response_mag, probe_mag)[0, 1]
        return float(correlation) if not np.isnan(correlation) else 0.0
    
    def compute_llr_from_metrics(self, metrics: ResponseMetrics) -> float:
        """Compute log-likelihood ratio from response metrics for APD.
        
        The LLR quantifies evidence for H1 (adaptive response) vs H0 (noise).
        
        LLR = (observation - H0_mean) * H1_shift / variance
        
        For RF anomaly detection:
            - H0: power ~ N(baseline_mean, baseline_std²)
            - H1: power ~ N(baseline_mean + signal, baseline_std²)
        
        Parameters
        ----------
        metrics : ResponseMetrics
            Response metrics.
        
        Returns
        -------
        float
            Log-likelihood ratio.
        """
        if self.baseline_mean is None or self.baseline_std is None:
            self.logger.warning("No baseline. LLR set to 0.")
            return 0.0
        
        # Observation: power_mean
        y = metrics.power_mean
        
        # H1 hypothesis: expected power = baseline + signal
        # Signal strength estimated from anomaly_score
        h1_mean = self.baseline_mean + self.anomaly_threshold * self.baseline_std
        
        # Variance
        variance = self.baseline_std ** 2
        
        # LLR for Gaussian: (y * mu - mu²/2) / sigma²
        # where mu = h1_mean - h0_mean
        mu_diff = h1_mean - self.baseline_mean
        llr = (y * mu_diff - 0.5 * mu_diff ** 2) / (variance + 1e-12)
        
        return float(llr)

"""
Active Beacon — APD-driven hydrogen line probe transmission and response detection.

Implements the probe-listen-adapt loop:
1. Select probe via APD policy (KL-optimal)
2. Transmit probe via HackRF
3. Listen for responses via RTL-SDR
4. Analyze response for anomalies
5. Update SPRT sequential test
6. Repeat until decision or max iterations

This is the main entry point for active protocol discovery experiments.
"""

import numpy as np
import subprocess
import time
import tempfile
import os
import json
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import sys

# Add paths for local imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../hydrogen-line-beacon'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../active-protocol-discovery'))

from hlb.rf import RFChannel
from hlb.monitor import Monitor
from hlb.constants import HYDROGEN_LINE_HZ

from apd import APDEngine, WaldSPRT, KLOptimalPolicy, APDResult
from apd.models import GaussianWorld

from .config import APDConfig
from .probe_library import ProbeLibrary, Probe, ProbeType
from .response_analyzer import ResponseAnalyzer, ResponseMetrics


class ActiveBeacon:
    """Active Protocol Discovery beacon using HLB and APD.
    
    Combines:
        - Hydrogen Line Beacon (HLB) for RF transmission
        - Active Protocol Discovery (APD) for sequential hypothesis testing
        - Statistical response analysis for anomaly detection
    
    Parameters
    ----------
    config : APDConfig
        Configuration for the APD session.
    verbose : bool
        Enable verbose logging.
    
    Example
    -------
    >>> config = APDConfig(
    ...     carrier_freq=433.92e6,  # ISM band (legal without license)
    ...     max_iterations=50,
    ...     probe_duration=5.0,
    ...     listen_duration=15.0,
    ... )
    >>> beacon = ActiveBeacon(config)
    >>> result = beacon.run()
    >>> print(f"Decision: {'Adaptive' if result.decision == 1 else 'Null'}")
    """
    
    def __init__(self, config: APDConfig, verbose: bool = True):
        self.config = config
        self.config.validate()
        
        # Setup logging
        self._setup_logging(verbose)
        
        # Create directories
        Path(self.config.log_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.temp_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.probe_library = ProbeLibrary(
            sample_rate=config.sample_rate,
            seed=config.probe_library_seed,
        )
        self.response_analyzer = ResponseAnalyzer(
            sample_rate=config.sample_rate,
            anomaly_threshold=config.anomaly_threshold_sigma,
        )
        
        # RF hardware
        self.rf_channel = RFChannel(
            carrier_freq=config.carrier_freq,
            sample_rate=config.sample_rate,
            tx_gain=config.tx_gain,
        )
        self.monitor = Monitor(log_dir=config.log_dir)
        
        # APD components (initialized in run())
        self.sprt = None
        self.policy = None
        self.apd_engine = None
        
        # Session state
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.probes = self.probe_library.get_standard_library()
        self.history: List[tuple[Probe, ResponseMetrics]] = []
        
        self.logger.info(f"ActiveBeacon initialized. Session: {self.session_id}")
        self.logger.info(f"Carrier: {config.carrier_freq / 1e6:.3f} MHz")
        self.logger.info(f"Probe library: {len(self.probes)} probes")
    
    def _setup_logging(self, verbose: bool):
        """Configure logging."""
        level = logging.INFO if verbose else logging.WARNING
        logging.basicConfig(
            level=level,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )
        self.logger = logging.getLogger(__name__)
    
    def check_hardware(self) -> dict:
        """Check if required hardware is available.
        
        Returns
        -------
        dict
            Hardware availability status.
        """
        hackrf_ok = RFChannel.is_available()
        rtlsdr_ok = self.monitor.is_available()
        
        status = {
            "hackrf": hackrf_ok,
            "rtlsdr": rtlsdr_ok,
            "ready": hackrf_ok and rtlsdr_ok,
        }
        
        self.logger.info(f"Hardware check: HackRF={hackrf_ok}, RTL-SDR={rtlsdr_ok}")
        
        if not status["ready"]:
            self.logger.warning("Missing required hardware!")
            if not hackrf_ok:
                self.logger.warning("  - HackRF One not found (needed for transmission)")
            if not rtlsdr_ok:
                self.logger.warning("  - RTL-SDR not found (needed for reception)")
        
        return status
    
    def capture_baseline(self, n_samples: int = 5) -> bool:
        """Capture baseline RF environment (no transmission).
        
        Parameters
        ----------
        n_samples : int
            Number of baseline samples to capture.
        
        Returns
        -------
        bool
            True if successful.
        """
        self.logger.info(f"Capturing baseline ({n_samples} samples)...")
        
        if not self.monitor.is_available():
            self.logger.error("RTL-SDR not available. Cannot capture baseline.")
            return False
        
        baseline_samples = []
        
        for i in range(n_samples):
            self.logger.info(f"  Baseline sample {i+1}/{n_samples}")
            
            # Capture IQ samples
            iq_file = f"{self.config.temp_dir}/baseline_{i}.iq"
            success = self.monitor.capture_iq(
                filename=iq_file,
                duration=self.config.listen_duration,
                freq=self.config.carrier_freq,
                sample_rate=self.config.sample_rate,
                gain=self.config.rx_gain,
            )
            
            if success and os.path.exists(iq_file):
                iq_data = np.fromfile(iq_file, dtype=np.int8)
                baseline_samples.append(iq_data)
            else:
                self.logger.warning(f"  Failed to capture baseline sample {i+1}")
            
            time.sleep(2)  # Brief pause between samples
        
        if len(baseline_samples) >= 2:
            self.response_analyzer.set_baseline(baseline_samples)
            self.logger.info("✓ Baseline established")
            return True
        else:
            self.logger.error("Failed to capture sufficient baseline samples")
            return False
    
    def run(self) -> APDResult:
        """Run the full Active Protocol Discovery session.
        
        Returns
        -------
        APDResult
            Result of the APD sequential test.
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting Active Protocol Discovery session")
        self.logger.info("=" * 60)
        
        # Hardware check
        hw_status = self.check_hardware()
        if not hw_status["ready"]:
            raise RuntimeError("Required hardware not available. Aborting.")
        
        # Capture baseline
        if not self.capture_baseline(self.config.baseline_samples):
            raise RuntimeError("Baseline capture failed. Aborting.")
        
        # Initialize APD components
        self.sprt = WaldSPRT(alpha=self.config.sprt_alpha, beta=self.config.sprt_beta)
        
        # KL-optimal policy: select probes by KL score
        self.policy = KLOptimalPolicy(
            probes=self.probes,
            sigma=self.response_analyzer.baseline_std or 1.0,
            mu_fn=lambda p: p.kl_score,  # Use probe's KL score as "mu"
        )
        
        # APD engine (we'll manually drive it for hardware integration)
        state = self.sprt.new_state()
        
        # Main probe-listen-adapt loop
        self.logger.info("\nStarting probe-listen-adapt loop...")
        self.logger.info(f"Max iterations: {self.config.max_iterations}")
        self.logger.info(f"SPRT thresholds: α={self.config.sprt_alpha}, β={self.config.sprt_beta}")
        
        probe_history = []
        
        for iteration in range(self.config.max_iterations):
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Iteration {iteration + 1}/{self.config.max_iterations}")
            self.logger.info(f"{'='*60}")
            
            # 1. Select probe (APD policy)
            probe = self.policy.select(history=self.history)
            self.logger.info(f"Selected probe: {probe.description}")
            self.logger.info(f"  Type: {probe.type.value}, KL score: {probe.kl_score:.2f}")
            
            # 2. Transmit probe
            iq_file = f"{self.config.temp_dir}/probe_{iteration}.iq"
            probe_iq = self.probe_library.generate_iq(probe, self.config.probe_duration)
            probe_iq.tofile(iq_file)
            
            self.logger.info(f"Transmitting probe for {self.config.probe_duration}s...")
            tx_process = self.rf_channel.transmit(iq_file, repeat=False)
            
            # Wait for transmission
            time.sleep(self.config.probe_duration + 0.5)
            
            # Stop transmission
            if tx_process and tx_process.poll() is None:
                tx_process.terminate()
                tx_process.wait(timeout=5)
            
            # 3. Inter-probe delay (allow settling)
            if self.config.inter_probe_delay > 0:
                self.logger.info(f"Inter-probe delay: {self.config.inter_probe_delay}s")
                time.sleep(self.config.inter_probe_delay)
            
            # 4. Listen for response
            response_file = f"{self.config.temp_dir}/response_{iteration}.iq"
            self.logger.info(f"Listening for response for {self.config.listen_duration}s...")
            
            capture_success = self.monitor.capture_iq(
                filename=response_file,
                duration=self.config.listen_duration,
                freq=self.config.carrier_freq + self.config.center_freq_offset,
                sample_rate=self.config.sample_rate,
                gain=self.config.rx_gain,
            )
            
            if not capture_success or not os.path.exists(response_file):
                self.logger.error("Response capture failed. Using zero observation.")
                response_iq = np.zeros(100, dtype=np.int8)
            else:
                response_iq = np.fromfile(response_file, dtype=np.int8)
            
            # 5. Analyze response
            metrics = self.response_analyzer.analyze(
                probe_id=iteration,
                response_iq=response_iq,
                probe_iq=probe_iq,
            )
            
            self.logger.info(f"Response analysis:")
            self.logger.info(f"  Power: {metrics.power_mean:.3e} ± {metrics.power_std:.3e}")
            self.logger.info(f"  SNR: {metrics.snr_db:.1f} dB")
            self.logger.info(f"  Anomaly score: {metrics.anomaly_score:.2f}σ")
            self.logger.info(f"  Correlation: {metrics.correlation:.3f}")
            self.logger.info(f"  Anomaly detected: {metrics.is_anomaly}")
            
            # 6. Compute LLR and update SPRT
            llr = self.response_analyzer.compute_llr_from_metrics(metrics)
            self.sprt.update(state, llr)
            
            self.logger.info(f"SPRT update:")
            self.logger.info(f"  LLR: {llr:.3f}")
            self.logger.info(f"  Cumulative log-odds: {state.log_likelihood_ratio:.3f}")
            self.logger.info(f"  Decision: {state.decision}")
            
            # Save history
            self.history.append((probe, metrics))
            probe_history.append(probe)
            
            # Log to file
            self._log_iteration(iteration, probe, metrics, llr, state)
            
            # 7. Check for decision
            if self.sprt.is_decided(state):
                decision_str = "H1 (Adaptive response detected)" if state.decision == 1 else "H0 (Null hypothesis)"
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"DECISION REACHED: {decision_str}")
                self.logger.info(f"Steps: {state.steps}")
                self.logger.info(f"{'='*60}")
                break
        
        # Construct result
        result = APDResult(
            decision=state.decision,
            steps=state.steps,
            log_odds_history=list(state.history),
            probes_used=probe_history,
        )
        
        self._save_session_summary(result)
        
        self.logger.info("\nSession complete.")
        return result
    
    def _log_iteration(self, iteration: int, probe: Probe, metrics: ResponseMetrics,
                       llr: float, sprt_state):
        """Log iteration data to JSON."""
        log_file = f"{self.config.log_dir}/{self.session_id}_iterations.jsonl"
        
        entry = {
            "session_id": self.session_id,
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "probe": {
                "type": probe.type.value,
                "description": probe.description,
                "kl_score": probe.kl_score,
            },
            "response": metrics.to_dict(),
            "sprt": {
                "llr": llr,
                "cumulative_log_odds": sprt_state.log_likelihood_ratio,
                "decision": sprt_state.decision,
                "steps": sprt_state.steps,
            },
        }
        
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def _save_session_summary(self, result: APDResult):
        """Save session summary to JSON."""
        summary_file = f"{self.config.log_dir}/{self.session_id}_summary.json"
        
        summary = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "config": self.config.to_dict(),
            "result": {
                "decision": result.decision,
                "decision_name": "H1 (Adaptive)" if result.decision == 1 else "H0 (Null)" if result.decision == 0 else "Undecided",
                "steps": result.steps,
                "log_odds_history": result.log_odds_history,
                "probes_used": [p.type.value for p in result.probes_used],
            },
            "hardware": self.check_hardware(),
        }
        
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(f"Summary saved: {summary_file}")


def main():
    """Command-line entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Active Protocol Discovery beacon for RF anomaly detection"
    )
    parser.add_argument(
        "--freq", type=float, default=433.92e6,
        help="Carrier frequency in Hz (default: 433.92 MHz ISM)"
    )
    parser.add_argument(
        "--hydrogen", action="store_true",
        help="Use hydrogen line (1420.405 MHz) — requires amateur radio license"
    )
    parser.add_argument(
        "--max-iter", type=int, default=50,
        help="Maximum iterations"
    )
    parser.add_argument(
        "--probe-duration", type=float, default=5.0,
        help="Probe transmission duration (seconds)"
    )
    parser.add_argument(
        "--listen-duration", type=float, default=15.0,
        help="Listen window duration (seconds)"
    )
    parser.add_argument(
        "--log-dir", type=str, default="./apd_logs",
        help="Log directory"
    )
    
    args = parser.parse_args()
    
    if args.hydrogen:
        freq = HYDROGEN_LINE_HZ
        print("⚠️  Using hydrogen line (1420.405 MHz)")
        print("   Ensure you have an amateur radio license before transmitting.")
    else:
        freq = args.freq
    
    config = APDConfig(
        carrier_freq=freq,
        max_iterations=args.max_iter,
        probe_duration=args.probe_duration,
        listen_duration=args.listen_duration,
        log_dir=args.log_dir,
        require_ham_license_confirm=False,  # CLI user has confirmed
    )
    
    beacon = ActiveBeacon(config)
    result = beacon.run()
    
    print("\n" + "="*60)
    if result.decision == 1:
        print("RESULT: Adaptive response detected (H1)")
    elif result.decision == 0:
        print("RESULT: Null hypothesis (H0) — no adaptive response")
    else:
        print("RESULT: Undecided (max iterations reached)")
    print(f"Steps: {result.steps}")
    print("="*60)


if __name__ == "__main__":
    main()

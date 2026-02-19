"""
Protocol Controller — The call-and-response state machine.
Coordinates RF transmission, mechanical transduction, and monitoring.
"""

import time
import os
import json
import signal
import tempfile
from datetime import datetime
from .constants import PROTOCOL_TX_DURATION, PROTOCOL_RX_DURATION, PROTOCOL_CYCLE_DURATION
from .rf import RFChannel
from .mechanical import MechanicalChannel
from .monitor import Monitor


class ProtocolState:
    """Protocol state tracking."""
    IDLE = "idle"
    TRANSMITTING = "transmitting"
    LISTENING = "listening"
    ANALYSING = "analysing"
    ADAPTING = "adapting"


class ProtocolController:
    """
    Call-and-response protocol state machine.
    
    Cycle:
        1. TRANSMIT  — Hydrogen line + Schumann + prime pulse
        2. LISTEN    — Monitor all channels for response
        3. ANALYSE   — Check for anomalies vs baseline
        4. ADAPT     — Adjust parameters based on response
        5. REPEAT    — Modified transmission
    
    The controller manages timing, synchronisation, and logging.
    """
    
    def __init__(self, config=None):
        self.config = config or self._default_config()
        self.state = ProtocolState.IDLE
        self.rf = None
        self.mech = MechanicalChannel()
        self.monitor = Monitor(log_dir=self.config.get('log_dir', './hlb_logs'))
        self.cycle_count = 0
        self.running = False
        self.session_id = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        # Session log
        self.session_log = []
    
    @staticmethod
    def _default_config():
        return {
            'rf_enabled': False,
            'rf_carrier': 1_420_405_751.768,
            'rf_gain': 20,
            'mech_programme': 'pulsed',
            'tx_duration': PROTOCOL_TX_DURATION,
            'rx_duration': PROTOCOL_RX_DURATION,
            'cycle_duration': PROTOCOL_CYCLE_DURATION,
            'total_duration': 3600,
            'anomaly_threshold': 3.0,
            'log_dir': './hlb_logs',
            'mech_wav': '/tmp/hlb_mech.wav',
        }
    
    def initialise(self):
        """Set up channels and capture baseline."""
        print("=" * 60)
        print("  HYDROGEN LINE BEACON — Protocol Controller")
        print("=" * 60)
        print(f"  Session:     {self.session_id}")
        print(f"  RF:          {'ENABLED' if self.config['rf_enabled'] else 'DISABLED'}")
        if self.config['rf_enabled']:
            print(f"  RF Carrier:  {self.config['rf_carrier']/1e6:.3f} MHz")
        print(f"  Mechanical:  {self.config['mech_programme']}")
        print(f"  Duration:    {self.config['total_duration']/60:.0f} min")
        print("=" * 60)
        
        # Initialise RF if enabled
        if self.config['rf_enabled']:
            self.rf = RFChannel(
                carrier_freq=self.config['rf_carrier'],
                tx_gain=self.config['rf_gain']
            )
            if not self.rf.is_available():
                print("\n  ⚠ HackRF not detected — RF channel disabled")
                self.rf = None
                self.config['rf_enabled'] = False
        
        # Generate mechanical WAV
        print("\n  Generating mechanical channel...")
        wav_file = self.config['mech_wav']
        cycle_dur = self.config['cycle_duration']
        self.mech.save_wav(wav_file, self.config['mech_programme'], cycle_dur)
        print(f"  ✓ Saved {wav_file}")
        
        # Generate RF baseband
        if self.rf:
            print("  Generating RF baseband...")
            self._rf_iq_file = '/tmp/hlb_rf.iq'
            self.rf.save_baseband(
                self._rf_iq_file,
                duration=self.config['tx_duration'],
                modulation='schumann',
                pulsed=True
            )
            print(f"  ✓ Saved {self._rf_iq_file}")
        
        # Capture baseline
        if self.monitor.is_available():
            print("\n  Capturing EM baseline...")
            self.monitor.capture_baseline(samples=3)
        else:
            print("\n  ⚠ RTL-SDR not detected — monitoring disabled")
        
        print("\n  Initialisation complete.\n")
    
    def run(self):
        """Execute the protocol loop."""
        self.running = True
        
        # Handle shutdown
        def _shutdown(sig, frame):
            print("\n  Shutdown requested...")
            self.running = False
        
        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)
        
        self.initialise()
        
        start_time = time.monotonic()
        total = self.config['total_duration']
        
        # Start continuous monitoring
        if self.monitor.is_available():
            self.monitor.start_continuous(
                interval=10,
                threshold_sigma=self.config['anomaly_threshold']
            )
        
        while self.running and (time.monotonic() - start_time) < total:
            self.cycle_count += 1
            cycle_start = time.monotonic()
            
            print(f"  ━━━ Cycle {self.cycle_count} ━━━")
            
            # Phase 1: TRANSMIT
            self._transmit_phase()
            
            if not self.running:
                break
            
            # Phase 2: LISTEN
            self._listen_phase()
            
            if not self.running:
                break
            
            # Phase 3: ANALYSE
            anomalies = self._analyse_phase()
            
            # Phase 4: ADAPT
            if anomalies:
                self._adapt_phase(anomalies)
            
            # Log cycle
            cycle_elapsed = time.monotonic() - cycle_start
            self._log('cycle_complete', {
                'cycle': self.cycle_count,
                'duration': cycle_elapsed,
                'anomalies_detected': len(anomalies) if anomalies else 0,
            })
            
            elapsed = time.monotonic() - start_time
            remaining = total - elapsed
            print(f"  ⏱ {remaining/60:.0f} min remaining\n")
        
        self._shutdown()
    
    def _transmit_phase(self):
        """Phase 1: Transmit on both channels."""
        self.state = ProtocolState.TRANSMITTING
        tx_dur = self.config['tx_duration']
        print(f"  ▶ TRANSMIT ({tx_dur}s)")
        
        # Start RF
        if self.rf:
            self.rf.transmit(self._rf_iq_file, repeat=True)
            print(f"    RF: {self.config['rf_carrier']/1e6:.3f} MHz")
        
        # Play mechanical (blocking for tx_duration)
        import subprocess
        try:
            proc = subprocess.Popen(
                ["aplay", self.config['mech_wav']],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            
            # Wait for tx_duration or until stopped
            start = time.monotonic()
            while self.running and (time.monotonic() - start) < tx_dur:
                time.sleep(0.5)
            
            proc.terminate()
            proc.wait(timeout=3)
        except FileNotFoundError:
            # aplay not available — just wait
            time.sleep(tx_dur)
        
        # Stop RF
        if self.rf:
            self.rf.stop()
        
        self._log('transmit', {'duration': tx_dur})
        print(f"    ✓ Transmit complete")
    
    def _listen_phase(self):
        """Phase 2: Passive listening."""
        self.state = ProtocolState.LISTENING
        rx_dur = self.config['rx_duration']
        print(f"  ◉ LISTEN ({rx_dur}s)")
        
        start = time.monotonic()
        while self.running and (time.monotonic() - start) < rx_dur:
            time.sleep(1)
        
        self._log('listen', {'duration': rx_dur})
        print(f"    ✓ Listen complete")
    
    def _analyse_phase(self):
        """Phase 3: Check for anomalies."""
        self.state = ProtocolState.ANALYSING
        print(f"  ◈ ANALYSE")
        
        anomalies = self.monitor.detect_anomalies(
            self.config['anomaly_threshold']
        )
        
        if anomalies:
            print(f"    ⚠ {len(anomalies)} anomalies detected!")
            for a in anomalies:
                print(f"      {a['frequency_hz']/1e6:.3f} MHz: "
                      f"{a['sigma']:.1f}σ ({a['power_db']:.1f} dB)")
                self.monitor.log_event('anomaly_in_cycle', {
                    **a,
                    'cycle': self.cycle_count
                })
        else:
            print(f"    No anomalies")
        
        self._log('analyse', {'anomaly_count': len(anomalies)})
        return anomalies
    
    def _adapt_phase(self, anomalies):
        """Phase 4: Adapt parameters based on detected anomalies."""
        self.state = ProtocolState.ADAPTING
        print(f"  ◆ ADAPT")
        
        # Future: adjust transmission parameters based on anomaly patterns
        # For now, log the adaptation opportunity
        strongest = max(anomalies, key=lambda a: abs(a['sigma']))
        print(f"    Strongest anomaly: {strongest['frequency_hz']/1e6:.3f} MHz "
              f"({strongest['sigma']:.1f}σ)")
        
        self._log('adapt', {
            'strongest_freq': strongest['frequency_hz'],
            'strongest_sigma': strongest['sigma'],
        })
    
    def _log(self, event_type, data):
        """Log protocol event."""
        entry = {
            'type': event_type,
            'session': self.session_id,
            'cycle': self.cycle_count,
            'state': self.state,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data,
        }
        self.session_log.append(entry)
        self.monitor.log_event(f'protocol_{event_type}', data)
    
    def _shutdown(self):
        """Clean shutdown."""
        print("\n  ■ Shutting down...")
        self.running = False
        
        if self.rf:
            self.rf.stop()
            print("    ✓ RF stopped")
        
        self.monitor.stop_continuous()
        print("    ✓ Monitor stopped")
        
        # Save session summary
        summary = {
            'session_id': self.session_id,
            'cycles': self.cycle_count,
            'config': {k: str(v) for k, v in self.config.items()},
            'events': len(self.session_log),
            'anomalies': sum(
                1 for e in self.session_log
                if e['type'] == 'analyse' and e['data'].get('anomaly_count', 0) > 0
            ),
        }
        
        summary_file = os.path.join(
            self.config['log_dir'],
            f"session_{self.session_id}.json"
        )
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"    ✓ Session saved to {summary_file}")
        print(f"\n  Session {self.session_id}: {self.cycle_count} cycles complete.\n")

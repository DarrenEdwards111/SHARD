"""
HydrogenLineBeacon — Main entry point.
High-level API for the complete beacon system.
"""

from .protocol import ProtocolController
from .rf import RFChannel
from .mechanical import MechanicalChannel
from .monitor import Monitor
from .constants import HYDROGEN_LINE_HZ, ISM_BANDS


class HydrogenLineBeacon:
    """
    Hydrogen Line Beacon — dual-channel electromechanical signal system.
    
    Quick start:
        from hlb import HydrogenLineBeacon
        
        beacon = HydrogenLineBeacon()
        beacon.run()  # mechanical only, 1 hour
        
        # With RF (requires HackRF One):
        beacon = HydrogenLineBeacon(rf=True)
        beacon.run()
        
        # ISM-legal (no ham licence needed):
        beacon = HydrogenLineBeacon(rf=True, freq='433')
        beacon.run()
        
        # Full hydrogen line (requires ham licence):
        beacon = HydrogenLineBeacon(rf=True, freq='hydrogen')
        beacon.run()
    """
    
    def __init__(self, rf=False, freq='hydrogen', duration=3600,
                 programme='full', gain=20, log_dir='./hlb_logs'):
        """
        Args:
            rf:        Enable RF channel (requires HackRF One)
            freq:      'hydrogen' (1.42 GHz), '433', '868', '2400', or Hz value
            duration:  Total session duration in seconds
            programme: Mechanical programme ('full', 'pulsed', 'combined', etc.)
            gain:      RF TX gain in dB (keep ≤20 for ISM compliance)
            log_dir:   Directory for event logs
        """
        # Resolve frequency
        if isinstance(freq, str):
            if freq == 'hydrogen':
                carrier = HYDROGEN_LINE_HZ
            elif freq in ISM_BANDS:
                carrier = ISM_BANDS[freq]['freq']
            else:
                carrier = float(freq)
        else:
            carrier = float(freq)
        
        self.config = {
            'rf_enabled': rf,
            'rf_carrier': carrier,
            'rf_gain': gain,
            'mech_programme': programme,
            'tx_duration': 60,
            'rx_duration': 120,
            'cycle_duration': 600,
            'total_duration': duration,
            'anomaly_threshold': 3.0,
            'log_dir': log_dir,
            'mech_wav': '/tmp/hlb_mech.wav',
        }
        
        self.controller = ProtocolController(self.config)
    
    def run(self):
        """Run the full protocol loop."""
        self.controller.run()
    
    def generate_mechanical(self, filename="hlb_output.wav", duration=3600,
                           programme="full"):
        """Generate just the mechanical channel WAV file."""
        mech = MechanicalChannel()
        mech.save_wav(filename, programme, duration)
        print(f"Generated {filename}")
        return filename
    
    def generate_rf_baseband(self, filename="hlb_baseband.iq", duration=60):
        """Generate just the RF baseband IQ file."""
        rf = RFChannel(carrier_freq=self.config['rf_carrier'])
        rf.save_baseband(filename, duration, modulation='schumann', pulsed=True)
        print(f"Generated {filename}")
        return filename
    
    def scan_baseline(self, samples=5):
        """Capture EM baseline without transmitting."""
        mon = Monitor(log_dir=self.config['log_dir'])
        if mon.is_available():
            mon.capture_baseline(samples)
        else:
            print("RTL-SDR not detected. Connect an RTL-SDR dongle.")
    
    def check_hardware(self):
        """Check what hardware is available."""
        print("Hardware check:")
        print(f"  HackRF One:  {'✓ Connected' if RFChannel.is_available() else '✗ Not found'}")
        print(f"  RTL-SDR:     {'✓ Connected' if Monitor.is_available() else '✗ Not found'}")
        print(f"  Audio (aplay): ", end="")
        import subprocess
        try:
            subprocess.run(["aplay", "--version"], capture_output=True, timeout=3)
            print("✓ Available")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("✗ Not found")
    
    @staticmethod
    def legal_info():
        """Print legal frequency information."""
        print("Legal frequencies (UK/EU, no licence required):")
        print()
        for name, band in ISM_BANDS.items():
            print(f"  {name} MHz ISM:")
            print(f"    Frequency:  {band['freq']/1e6:.2f} MHz")
            print(f"    Max power:  {band['max_power_mw']} mW")
            print(f"    Region:     {band['region']}")
            print()
        print("Hydrogen line (1420.405 MHz):")
        print("  Requires amateur radio licence (Foundation minimum)")
        print("  UK: Ofcom Foundation Licence, one-day course, ~£50")
        print()
        print("⚠ Transmitting outside ISM bands without a licence is illegal.")

"""
Command-line interface for the Hydrogen Line Beacon.
"""

import argparse
from .beacon import HydrogenLineBeacon


def main():
    parser = argparse.ArgumentParser(
        description="Hydrogen Line Beacon — Dual-channel electromechanical signal system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  hlb                              Mechanical only, 1 hour
  hlb --rf                         Both channels (requires HackRF)
  hlb --rf --freq 433              ISM-legal RF (no licence needed)
  hlb --rf --freq hydrogen         1.42 GHz hydrogen line (needs ham licence)
  hlb --duration 1800              30 minutes
  hlb --programme pulsed           Prime-number pulse timing
  hlb --generate mech.wav          Generate WAV only (no playback)
  hlb --check                      Check connected hardware
  hlb --legal                      Print legal frequency info

Programmes:
  full          Complete protocol cycle (recommended)
  pulsed        Schumann + prime-number pulse gating
  combined      All 5 Schumann modes simultaneously
  fundamental   7.83 Hz only
  scan          Step through Schumann harmonics
  chirp         Sweep 1-20 Hz
  breathing     7.83 Hz with breathing envelope
        """
    )
    
    parser.add_argument('--rf', action='store_true',
                       help='Enable RF channel (requires HackRF One)')
    parser.add_argument('--freq', type=str, default='hydrogen',
                       help='RF frequency: hydrogen, 433, 868, 2400, or Hz value (default: hydrogen)')
    parser.add_argument('--duration', type=int, default=3600,
                       help='Duration in seconds (default: 3600)')
    parser.add_argument('--programme', type=str, default='full',
                       choices=['full', 'pulsed', 'combined', 'fundamental', 'scan', 'chirp', 'breathing'],
                       help='Signal programme (default: full)')
    parser.add_argument('--gain', type=int, default=20,
                       help='RF TX gain in dB (default: 20, keep ≤20 for ISM)')
    parser.add_argument('--log-dir', type=str, default='./hlb_logs',
                       help='Log directory (default: ./hlb_logs)')
    parser.add_argument('--generate', type=str, metavar='FILE',
                       help='Generate WAV file only (no playback/protocol)')
    parser.add_argument('--generate-rf', type=str, metavar='FILE',
                       help='Generate RF baseband IQ file only')
    parser.add_argument('--check', action='store_true',
                       help='Check connected hardware')
    parser.add_argument('--legal', action='store_true',
                       help='Print legal frequency information')
    parser.add_argument('--baseline', action='store_true',
                       help='Capture EM baseline only (no transmission)')
    
    args = parser.parse_args()
    
    beacon = HydrogenLineBeacon(
        rf=args.rf,
        freq=args.freq,
        duration=args.duration,
        programme=args.programme,
        gain=args.gain,
        log_dir=args.log_dir,
    )
    
    if args.check:
        beacon.check_hardware()
    elif args.legal:
        beacon.legal_info()
    elif args.generate:
        beacon.generate_mechanical(args.generate, args.duration, args.programme)
    elif args.generate_rf:
        beacon.generate_rf_baseband(args.generate_rf, min(args.duration, 60))
    elif args.baseline:
        beacon.scan_baseline()
    else:
        beacon.run()


if __name__ == '__main__':
    main()

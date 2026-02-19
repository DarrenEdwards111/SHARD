"""
Hydrogen Line Beacon (HLB)
A dual-channel electromechanical signal system for the Raspberry Pi 5.

Channels:
  1. RF — 1.42 GHz hydrogen line carrier, Schumann AM modulation, prime pulse timing
  2. Mechanical — Ground-coupled seismic transduction at Schumann frequencies

Requires: numpy, scipy
Optional: hackrf (for RF channel), sounddevice (for live playback)
"""

__version__ = "0.1.0"
__author__ = "Mikoshi Ltd"

from .beacon import HydrogenLineBeacon
from .rf import RFChannel
from .mechanical import MechanicalChannel
from .protocol import ProtocolController
from .monitor import Monitor

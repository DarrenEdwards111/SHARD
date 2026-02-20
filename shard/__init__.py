"""
SHARD — Schumann Hydrogen Active RF Discovery

Sequential hypothesis testing for active RF anomaly detection.
Combines the Hydrogen Line Beacon (HLB) with Active Protocol Discovery (APD)
for statistical analysis of radio-frequency responses.
"""

__version__ = "1.0.0"
__author__ = "Darren Edwards"
__email__ = "darrenedwards111@gmail.com"
__license__ = "Apache-2.0"

from .active_beacon import ActiveBeacon
from .probe_library import ProbeLibrary, ProbeType
from .response_analyzer import ResponseAnalyzer
from .config import APDConfig

# Re-export HLB components
from . import hlb

__all__ = [
    "ActiveBeacon",
    "ProbeLibrary",
    "ProbeType",
    "ResponseAnalyzer",
    "APDConfig",
    "hlb",
    "__version__",
]

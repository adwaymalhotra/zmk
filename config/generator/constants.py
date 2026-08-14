"""
Global constants and modifier helpers for ZMK generator.
"""

PRIOR_IDLE_MS = 160
QUICK_TAP_MS = 175
TAPPING_TERM = 200
COMBO_TERM = 50

# Standard modifier strings
ALT = "LALT"
SFT = "LSHFT"
CTL = "LCTL"
MET = "LGUI"
GUI = "LGUI"

# Modifier wrapper helpers
def S(key: str) -> str: return f"LS({key})"
def C(key: str) -> str: return f"LC({key})"
def A(key: str) -> str: return f"LA({key})"
def G(key: str) -> str: return f"LG({key})"

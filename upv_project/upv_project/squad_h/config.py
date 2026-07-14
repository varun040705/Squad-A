"""
config.py

Configuration constants for the Acoustic Emission (AE) Context Engine.

Author: Sai Varun
Project: OX1 - Squad H
"""

# ==========================================
# Localization
# ==========================================

MIN_LOCALIZATION_SENSORS = 4


# ==========================================
# Confidence
# ==========================================

CONFIDENCE_CEILING = 60.0


# ==========================================
# Noise Detection
# ==========================================

MIN_AMPLITUDE = 20.0          # dB (placeholder)
MIN_ENERGY = 10.0             # aJ (placeholder)
MIN_COUNTS = 5


# ==========================================
# Trend Analysis
# ==========================================

MIN_HITS_FOR_TREND = 20

WINDOW_SIZE = 60              # seconds


# ==========================================
# Grade Enumeration
# ==========================================

VALID_GRADES = (
    "I",
    "II",
    "III",
    "IV",
)
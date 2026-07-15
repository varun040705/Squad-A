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
# Per workplan H-1: rise_time / duration > 0.5 is the noise-rejection rule.

NOISE_RISE_TIME_TO_DURATION_RATIO = 0.5


# ==========================================
# Trend Analysis (b-value)
# ==========================================

MIN_HITS_FOR_TREND = 20        # per-window minimum before a b-value is attempted

WINDOW_SIZE = 60               # seconds, size of each time bin for trending

MIN_WINDOWS_FOR_TREND = 3      # need >=3 windows to say anything about a trend

B_VALUE_DECLINE_SLOPE_THRESHOLD = -0.01
# slope of b-value vs. window index; more negative than this => "declining"


# ==========================================
# Localization
# ==========================================
# NOTE: real triangulation needs known sensor coordinates and a wave
# velocity for the monitored element. These are element-specific and must
# be supplied by the caller (see SensorGeometry in models.py).

DEFAULT_WAVE_VELOCITY_MPS = 4000.0   # typical P-wave velocity in concrete, m/s


# ==========================================
# Severity Grading (Felicity ratio / calm ratio)
# ==========================================

FELICITY_GRADE_II_MIN = 0.95    # 0.95 <= FR < 1.0  -> Grade II
FELICITY_GRADE_III_MIN = 0.80   # 0.80 <= FR < 0.95 -> Grade III
                                 # FR < 0.80         -> Grade IV

CALM_RATIO_HIGH_THRESHOLD = 0.3  # calm_ratio above this -> Grade IV regardless of FR
                                  # (placeholder -- confirm this number against
                                  # JCMS/NDIS-2421 reference tables before production use)
# ==========================================
# Grade Enumeration
# ==========================================

VALID_GRADES = (
    "I",
    "II",
    "III",
    "IV",
)
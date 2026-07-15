"""
models.py

Pydantic models for the Acoustic Emission (AE) Context Engine.

Author: Sai Varun
Project: OX1 - Squad H
"""

from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field

# --------------------------------------------------
# Common Enums
# --------------------------------------------------

class AEGrade(str, Enum):
    I = "I"
    II = "II"
    III = "III"
    IV = "IV"

class TrendType(str, Enum):
    INCREASING = "Increasing"
    STABLE = "Stable"
    DECREASING = "Decreasing"
    INSUFFICIENT_DATA = "Insufficient Data"


class LoadPhase(str, Enum):
    LOADING = "loading"
    UNLOADING = "unloading"
    RELOADING = "reloading"


# --------------------------------------------------
# Input : Sensor Geometry (required for real localization)
# --------------------------------------------------

class SensorGeometry(BaseModel):
    """
    Known sensor position, needed to solve Δt_ij = (distance_i - distance_j) / wave_velocity.
    """

    sensor_id: str
    x: float
    y: float
    z: float


# --------------------------------------------------
# Input : Load History Sample (required for calm/Felicity ratio)
# --------------------------------------------------

class LoadSample(BaseModel):
    """
    A single load-cell reading correlated against the AE monitoring timeline.
    """

    timestamp: float
    load: float
    phase: LoadPhase


# --------------------------------------------------
# H1 : Acoustic Emission Hit
# --------------------------------------------------

class AEHit(BaseModel):
    sensor_id: str
    timestamp: float

    amplitude: float = Field(..., ge=0)
    duration: float = Field(..., ge=0)
    energy: float = Field(..., ge=0)
    rise_time: float = Field(..., ge=0)
    counts: int = Field(..., ge=0)
    peak_frequency: float = Field(..., ge=0)

    is_noise: bool = False
    quality_score: float = Field(..., ge=0, le=100)

# --------------------------------------------------
# H1 : Preprocessing Result
# --------------------------------------------------

class H1Result(BaseModel):
    """
    Output of the H-1 preprocessing stage.
    """

    raw_hits: list[AEHit]
    eligible_hits: list[AEHit]
    flags: list[str] = Field(default_factory=list)

# --------------------------------------------------
# H2 : Localization
# --------------------------------------------------

class LocalizationResult(BaseModel):
    success: bool

    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None

    sensors_used: int

    message: str


# --------------------------------------------------
# H2 : Trend Analysis
# --------------------------------------------------

class TrendResult(BaseModel):

    b_value: Optional[float] = None

    trend: TrendType

    confidence: float = Field(..., ge=0, le=100)
# --------------------------------------------------
# H2 : Load History
# --------------------------------------------------

class LoadHistoryResult(BaseModel):

    calm_ratio: Optional[float] = None
    felicity_ratio: Optional[float] = None

    previous_peak_load: Optional[float] = None
    current_peak_load: Optional[float] = None

# --------------------------------------------------
# H2 : Analysis Result
# --------------------------------------------------

class H2Result(BaseModel):
    """
    Output of the H-2 analysis stage.
    """

    localization: LocalizationResult
    trend: TrendResult
    load_history: LoadHistoryResult

    total_hits: int
    eligible_hits: int

    flags: list[str] = Field(default_factory=list)

# --------------------------------------------------
# H3 : Final Context (published downstream to Sensor Fusion)
# --------------------------------------------------
# Flattened to match the exact contract in the workplan.

class AcousticEmissionContext(BaseModel):

    method: str = "AE"
    element_ref: str
    inspection_id: str

    hits_total: int
    hits_localized: int

    b_value_trend: TrendType
    felicity_ratio: Optional[float] = None
    calm_ratio: Optional[float] = None

    grade: Optional[AEGrade] = None
    confidence: float = Field(..., ge=0, le=100)
    confidence_ceiling: int = 60

    flags: list[str] = Field(default_factory=list)

    summary: str
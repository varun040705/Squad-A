"""
models.py

Pydantic models for the Defect Detection Engine.

Author: Sai Varun
Project: OX1 - Defect Engine
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --------------------------------------------------
# Enumerations
# --------------------------------------------------

class DefectType(str, Enum):
    CRACK = "Crack"
    CORROSION = "Corrosion"
    FATIGUE = "Fatigue"
    VIBRATION = "Vibration Anomaly"
    UNKNOWN = "Unknown"


class SeverityLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


# --------------------------------------------------
# Dataset Record
# --------------------------------------------------

class BridgeRecord(BaseModel):

    timestamp: str

    acoustic_emission: float

    crack_propagation: float

    corrosion_level: float

    fatigue_accumulation: float

    structural_health_index: float

    anomaly_score: float

    probability_of_failure: float

    maintenance_alert: bool

# --------------------------------------------------
# Defect
# --------------------------------------------------

class Defect(BaseModel):

    defect_id: str

    defect_type: DefectType

    severity: SeverityLevel

    confidence: float = Field(..., ge=0, le=100)

    evidence: list[str]

    recommendation: str


# --------------------------------------------------
# Final Detection Result
# --------------------------------------------------

class DefectDetectionResult(BaseModel):

    total_records: int

    total_defects: int

    defects: list[Defect]

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any

class CorrectionEntry(BaseModel):
    type: str
    factor: float
    reason: str

class EffectiveBands(BaseModel):
    critical: float
    severe: float
    moderate: float

class VisualContextOutput(BaseModel):
    success: bool = True
    input_id: str
    raw_crack_width_mm: float
    corrected_crack_width_mm: float
    corrections_applied: List[CorrectionEntry]
    effective_bands: EffectiveBands
    confidence_ceiling: int
    flags: List[str]

    @field_validator("confidence_ceiling")
    @classmethod
    def validate_ceiling(cls, value: int) -> int:
        if not (0 <= value <= 100):
            raise ValueError("Confidence ceiling must be between 0 and 100.")
        return value

class ClaudeResponseSchema(BaseModel):
    primary_defect: str = Field(..., description="Name of the defect identified or 'none'.")
    flag_score: int = Field(..., ge=0, le=100)
    recommended_action: str = Field(..., description="Action directive category, e.g., monitor, escalate")
    reasoning: str = Field(..., min_length=15)

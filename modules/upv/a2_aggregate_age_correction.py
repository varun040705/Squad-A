"""
OX1 NDT Platform - UPV Module
Squad A - Segment A-2: Aggregate Thresholds & Age Maturity Index

This module:
1. Selects aggregate-aware quality threshold bands.
2. Computes Age Maturity Index (AMI).
3. Flags age underperformance when AMI < 0.85.
"""

from typing import Dict, Tuple, Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, field_validator


# =====================================================================
# ENUMS
# =====================================================================

class AggregateType(str, Enum):
    standard = "standard"
    lightweight = "lightweight"


# =====================================================================
# CONSTANTS
# =====================================================================

DENSE_BANDS = {
    "excellent": 4.5,
    "good": 3.5,
    "medium": 3.0,
    "poor": 3.0
}

LIGHTWEIGHT_BANDS = {
    "excellent": 3.2,
    "good": 2.5,
    "medium": 2.0,
    "poor": 1.8
}

AGE_MATURITY = {
    3: 0.58,
    7: 0.74,
    14: 0.88,
    28: 1.00,
    90: 1.12
}

AMI_THRESHOLD = 0.85


# =====================================================================
# PYDANTIC SCHEMAS
# =====================================================================

class CorrectionLogEntry(BaseModel):
    type: str = Field(...)
    factor: float = Field(...)
    reason: str = Field(...)


class AggregateAgeInput(BaseModel):
    element_id: UUID = Field(...)
    aggregate_type: AggregateType = Field(...)
    concrete_age_days: int = Field(...)
    raw_velocity_kmps: float = Field(...)
    v_28day_reference: float = Field(...)

    @field_validator("raw_velocity_kmps", "v_28day_reference")
    @classmethod
    def validate_positive_velocity(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Velocity values must be positive.")
        return v


class AggregateAgeContext(BaseModel):
    element_id: UUID

    effective_bands: Dict[str, float]

    age_mismatch_index: Optional[float]

    age_underperformance: bool

    corrections_applied: List[CorrectionLogEntry]


# =====================================================================
# PROCESSING FUNCTIONS
# =====================================================================

def get_effective_bands(
    aggregate_type: AggregateType
) -> Dict[str, float]:
    """
    Return threshold bands based on aggregate type.
    """

    if aggregate_type == AggregateType.lightweight:
        return LIGHTWEIGHT_BANDS

    return DENSE_BANDS


def compute_ami(
    v_actual: float,
    age_days: int,
    v_28day_reference: float
) -> Tuple[Optional[float], bool]:
    """
    Compute Age Maturity Index.

    AMI = V_actual / V_expected_for_age

    V_expected_for_age =
        v_28day_reference * maturity_factor
    """

    expected_factor = AGE_MATURITY.get(age_days)

    if expected_factor is None:
        return None, True

    v_expected = v_28day_reference * expected_factor

    ami = round(v_actual / v_expected, 3)

    return ami, ami < AMI_THRESHOLD


def assemble_context(
    input_data: Dict
) -> AggregateAgeContext:
    """
    Build aggregate threshold and AMI context.
    """

    validated_input = AggregateAgeInput(**input_data)

    corrections: List[CorrectionLogEntry] = []

    effective_bands = get_effective_bands(
        validated_input.aggregate_type
    )

    ami, underperformance = compute_ami(
        v_actual=validated_input.raw_velocity_kmps,
        age_days=validated_input.concrete_age_days,
        v_28day_reference=validated_input.v_28day_reference
    )

    if ami is None:
        corrections.append(
            CorrectionLogEntry(
                type="age_maturity",
                factor=0.0,
                reason=f"unsupported age {validated_input.concrete_age_days}"
            )
        )

    return AggregateAgeContext(
        element_id=validated_input.element_id,
        effective_bands=effective_bands,
        age_mismatch_index=ami,
        age_underperformance=underperformance,
        corrections_applied=corrections
    )
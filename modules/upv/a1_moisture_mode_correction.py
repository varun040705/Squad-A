"""
OX1 NDT Platform - UPV Module
Squad A - Segment A-1: Moisture & Mode Correction Module

This module takes a raw velocity and applies moisture and transmission mode corrections.
It logs applied corrections and enforces confidence ceilings based on transmission modes.
"""

from typing import List, Optional, Tuple, Dict
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator


# =====================================================================
# CONSTANTS & CONFIGURATION
# =====================================================================

# Moisture Correction Factors (reduction percentage stored as negative float)
MOISTURE_FACTORS = {
    "dry": 0.00,
    "slightly_damp": -0.04,
    "damp": -0.09,
    "wet": -0.18,
    "saturated": -0.25
}

# Transmission Mode Penalties (reduction percentage stored as negative float)
MODE_PENALTIES = {
    "direct": 0.00,
    "semi_direct": -0.07,
    "indirect": -0.13
}

# Default Confidence Settings
CONFIDENCE_CEILING_DEFAULT = 100
CONFIDENCE_CEILING_INDIRECT = 60


# =====================================================================
# PYDANTIC SCHEMAS (V2)
# =====================================================================

class CorrectionLogEntry(BaseModel):
    """
    Log entry for any correction applied to a velocity reading.
    """
    type: str = Field(..., description="The type of correction applied (e.g. 'moisture', 'mode')")
    factor: float = Field(..., description="The factor applied as a negative float (e.g. -0.18)")
    reason: str = Field(..., description="The condition causing the correction (e.g. 'wet condition')")


class UPVInputReading(BaseModel):
    """
    Validates input data for Segment A-1.
    """
    element_id: UUID = Field(..., description="The unique ID of the concrete element")
    raw_velocity_kmps: float = Field(..., description="The measured raw velocity in km/s")
    moisture_condition: str = Field(..., description="Moisture state: dry, slightly_damp, damp, wet, saturated")
    transmission_mode: str = Field(..., description="Sensor transmission mode: direct, semi_direct, indirect")

    @field_validator("moisture_condition")
    @classmethod
    def validate_moisture(cls, v: str) -> str:
        v_clean = v.lower().strip()
        if v_clean not in MOISTURE_FACTORS:
            raise ValueError(f"Unknown moisture condition '{v}'. Must be one of: {list(MOISTURE_FACTORS.keys())}")
        return v_clean

    @field_validator("transmission_mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        v_clean = v.lower().strip()
        if v_clean not in MODE_PENALTIES:
            raise ValueError(f"Unknown transmission mode '{v}'. Must be one of: {list(MODE_PENALTIES.keys())}")
        return v_clean

    @field_validator("raw_velocity_kmps")
    @classmethod
    def validate_raw_velocity(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Raw velocity must be positive.")
        return v


class UPVReadingContext(BaseModel):
    """
    Validated context output for Segment A-1.
    """
    element_id: UUID = Field(..., description="Unique ID of the concrete element")
    raw_velocity_kmps: float = Field(..., description="Original raw velocity in km/s")
    moisture_corrected_velocity: float = Field(..., description="Velocity in km/s after moisture and mode corrections")
    corrections_applied: List[CorrectionLogEntry] = Field(..., description="Chronological log of corrections applied")
    confidence_ceiling: int = Field(..., description="Maximum allowed confidence score (0-100)")

    @field_validator("raw_velocity_kmps", "moisture_corrected_velocity")
    @classmethod
    def validate_velocities(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Velocity must be greater than zero.")
        return round(v, 4)


# =====================================================================
# CALCULATION & PROCESSING FUNCTIONS
# =====================================================================

def apply_moisture_correction(raw_velocity: float, moisture_condition: str) -> Tuple[float, Optional[CorrectionLogEntry]]:
    """
    Applies moisture correction factor.
    Returns the corrected velocity and a log entry if a correction occurred.
    """
    factor = MOISTURE_FACTORS[moisture_condition]
    corrected = raw_velocity * (1.0 + factor)
    
    # Stored as negative float if there is a change, or log direct representation
    log = None
    if factor != 0.0:
        log = CorrectionLogEntry(
            type="moisture",
            factor=factor,
            reason=f"{moisture_condition} condition"
        )
    return round(corrected, 4), log


def apply_moisture_and_mode_corrections(
    raw_velocity: float,
    moisture_condition: str,
    transmission_mode: str
) -> Tuple[float, List[CorrectionLogEntry], int]:
    """
    Applies moisture correction first, then transmission mode penalty.
    Logs each correction applied to the corrections_applied list.
    Enforces a confidence ceiling of 60 if transmission mode is indirect.
    """
    corrections: List[CorrectionLogEntry] = []
    
    # 1. Moisture Correction
    moisture_corrected, moisture_log = apply_moisture_correction(raw_velocity, moisture_condition)
    if moisture_log is not None:
        corrections.append(moisture_log)

    # 2. Transmission Mode Penalty
    mode_penalty = MODE_PENALTIES[transmission_mode]
    final_corrected = moisture_corrected
    if mode_penalty != 0.0:
        final_corrected = final_corrected * (1.0 + mode_penalty)
        corrections.append(CorrectionLogEntry(
            type="mode",
            factor=mode_penalty,
            reason=f"{transmission_mode.replace('_', '-')} transmission"
        ))

    # 3. Confidence Ceiling Effect
    confidence_ceiling = CONFIDENCE_CEILING_DEFAULT
    if transmission_mode == "indirect":
        confidence_ceiling = CONFIDENCE_CEILING_INDIRECT

    return round(final_corrected, 4), corrections, confidence_ceiling


def assemble_context(input_data: Dict) -> UPVReadingContext:
    """
    Entrypoint: Takes raw input data, performs corrections, and validates the output structure.
    """
    # 1. Validate inputs
    validated_input = UPVInputReading(**input_data)

    # 2. Apply corrections
    corrected_vel, corrections, ceiling = apply_moisture_and_mode_corrections(
        raw_velocity=validated_input.raw_velocity_kmps,
        moisture_condition=validated_input.moisture_condition,
        transmission_mode=validated_input.transmission_mode
    )

    # 3. Assemble and return context schema
    return UPVReadingContext(
        element_id=validated_input.element_id,
        raw_velocity_kmps=validated_input.raw_velocity_kmps,
        moisture_corrected_velocity=corrected_vel,
        corrections_applied=corrections,
        confidence_ceiling=ceiling
    )

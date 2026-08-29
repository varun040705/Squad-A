"""
OX1 NDT Platform - Dimensional Inspection Module
Squad A - Segment DIM-1: Concrete Clearance Cover QA (ACI 117) & Floor Flatness/Levelness (ASTM E1155)
"""

import math
from typing import List, Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class FlatnessClassification(str, Enum):
    conventional = "conventional"   # FF 20 / FL 15
    flat = "flat"                   # FF 30 / FL 20
    very_flat = "very_flat"         # FF 50 / FL 35
    super_flat = "super_flat"       # FF 100 / FL 50
    non_compliant = "non_compliant"


class DimensionalDataFlags(BaseModel):
    missing_element_ref: bool = Field(False, description="Element reference missing")
    no_cover_data: bool = Field(False, description="No concrete cover readings provided")
    insufficient_cover_readings: bool = Field(False, description="Fewer than 5 cover readings")
    cover_out_of_tolerance: bool = Field(False, description="One or more cover readings violate ACI 117 tolerance")
    no_flatness_data: bool = Field(False, description="No floor elevation points provided")


class DimensionalInspectionInput(BaseModel):
    element_ref: str = Field(..., description="Structural element identifier")
    nominal_cover_mm: float = Field(40.0, description="Specified nominal concrete cover in mm")
    measured_covers_mm: List[float] = Field(default_factory=list, description="Measured rebar cover values in mm")
    elevation_readings_mm: List[float] = Field(default_factory=list, description="Floor elevation profile readings in mm")
    sample_spacing_m: float = Field(3.0, description="Elevation point grid spacing in meters per ASTM E1155")

    @field_validator("nominal_cover_mm")
    @classmethod
    def validate_nominal_cover(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("nominal_cover_mm must be positive.")
        return v


class DimensionalInspectionContext(BaseModel):
    element_ref: str = Field(..., description="Structural element identifier")
    nominal_cover_mm: float = Field(..., description="Specified nominal concrete cover")
    mean_cover_mm: Optional[float] = Field(None, description="Average measured concrete cover in mm")
    min_cover_mm: Optional[float] = Field(None, description="Minimum measured cover in mm")
    max_cover_mm: Optional[float] = Field(None, description="Maximum measured cover in mm")
    cover_compliance_pct: Optional[float] = Field(None, description="Percentage of cover readings within ACI 117 tolerance")
    ff_flatness_number: Optional[float] = Field(None, description="ASTM E1155 Floor Flatness Number FF")
    fl_levelness_number: Optional[float] = Field(None, description="ASTM E1155 Floor Levelness Number FL")
    flatness_class: Optional[FlatnessClassification] = Field(None, description="Overall floor quality classification")
    confidence_ceiling: int = Field(100, description="Reliability score 0-100%")
    flags: DimensionalDataFlags = Field(..., description="Quality and validation flags")
    has_errors: bool = Field(False, description="True if mandatory data is missing")


def evaluate_aci117_cover_tolerance(nominal_mm: float) -> tuple[float, float]:
    """
    ACI 117 cover tolerances:
    For nominal cover <= 50 mm: -10 mm / +15 mm
    For nominal cover > 50 mm: -12 mm / +20 mm
    """
    if nominal_mm <= 50.0:
        return nominal_mm - 10.0, nominal_mm + 15.0
    else:
        return nominal_mm - 12.0, nominal_mm + 20.0


def calculate_astm_e1155_flatness(elevations: List[float]) -> tuple[Optional[float], Optional[float]]:
    """
    ASTM E1155 F-Numbers:
    FF = 4.57 / Sq (where Sq is std dev of elevation differences between adjacent points d_i = y_{i+1} - y_i)
    FL = 4.57 / Sz (where Sz is std dev of elevation differences across 2-step intervals z_i = y_{i+2} - y_i)
    """
    if len(elevations) < 4:
        return None, None

    # 1-step differences (curvature differences for FF)
    d_vals = [elevations[i+1] - elevations[i] for i in range(len(elevations) - 1)]
    mean_d = sum(d_vals) / len(d_vals)
    var_d = sum((d - mean_d)**2 for d in d_vals) / (len(d_vals) - 1)
    sq = math.sqrt(var_d) if var_d > 0 else 0.001

    # 2-step differences (levelness differences for FL)
    z_vals = [elevations[i+2] - elevations[i] for i in range(len(elevations) - 2)]
    mean_z = sum(z_vals) / len(z_vals)
    var_z = sum((z - mean_z)**2 for z in z_vals) / (len(z_vals) - 1)
    sz = math.sqrt(var_z) if var_z > 0 else 0.001

    ff = round(4.57 / sq, 1) if sq > 0 else 100.0
    fl = round(4.57 / sz, 1) if sz > 0 else 100.0

    return max(ff, 1.0), max(fl, 1.0)


def classify_flatness(ff: float, fl: float) -> FlatnessClassification:
    """
    Classifies ASTM E1155 F-Numbers.
    """
    if ff >= 100.0 and fl >= 50.0:
        return FlatnessClassification.super_flat
    elif ff >= 50.0 and fl >= 35.0:
        return FlatnessClassification.very_flat
    elif ff >= 30.0 and fl >= 20.0:
        return FlatnessClassification.flat
    elif ff >= 20.0 and fl >= 15.0:
        return FlatnessClassification.conventional
    else:
        return FlatnessClassification.non_compliant


def run_dimensional_engine(raw_input: Dict) -> DimensionalInspectionContext:
    inp = DimensionalInspectionInput(**raw_input)

    flags = DimensionalDataFlags(
        missing_element_ref=not inp.element_ref.strip(),
        no_cover_data=(len(inp.measured_covers_mm) == 0),
        insufficient_cover_readings=(0 < len(inp.measured_covers_mm) < 5),
        cover_out_of_tolerance=False,
        no_flatness_data=(len(inp.elevation_readings_mm) < 4)
    )

    has_errors = flags.no_cover_data and flags.no_flatness_data

    if has_errors:
        return DimensionalInspectionContext(
            element_ref=inp.element_ref,
            nominal_cover_mm=inp.nominal_cover_mm,
            confidence_ceiling=0,
            flags=flags,
            has_errors=True
        )

    # Cover Calculations
    mean_cover = None
    min_cover = None
    max_cover = None
    compliance_pct = None
    if inp.measured_covers_mm:
        min_allowed, max_allowed = evaluate_aci117_cover_tolerance(inp.nominal_cover_mm)
        mean_cover = round(sum(inp.measured_covers_mm) / len(inp.measured_covers_mm), 1)
        min_cover = min(inp.measured_covers_mm)
        max_cover = max(inp.measured_covers_mm)
        
        valid_count = sum(1 for c in inp.measured_covers_mm if min_allowed <= c <= max_allowed)
        compliance_pct = round((valid_count / len(inp.measured_covers_mm)) * 100.0, 1)
        flags.cover_out_of_tolerance = (compliance_pct < 100.0)

    # Flatness Calculations
    ff, fl = calculate_astm_e1155_flatness(inp.elevation_readings_mm)
    flatness_class = classify_flatness(ff, fl) if (ff and fl) else None

    # Confidence Score Calculation
    score = 100
    if flags.insufficient_cover_readings:
        score -= 20
    if flags.cover_out_of_tolerance:
        score -= 15
    if flags.no_flatness_data:
        score -= 15
    if flags.missing_element_ref:
        score -= 10

    return DimensionalInspectionContext(
        element_ref=inp.element_ref,
        nominal_cover_mm=inp.nominal_cover_mm,
        mean_cover_mm=mean_cover,
        min_cover_mm=min_cover,
        max_cover_mm=max_cover,
        cover_compliance_pct=compliance_pct,
        ff_flatness_number=ff,
        fl_levelness_number=fl,
        flatness_class=flatness_class,
        confidence_ceiling=max(0, min(score, 100)),
        flags=flags,
        has_errors=False
    )

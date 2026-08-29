"""
OX1 NDT Platform - Laboratory Testing Module
Squad A - Segment LAB-1: Compressive Cylinder Strength (ASTM C39), Split-Tensile (ASTM C496) & ACI 318 Acceptance
"""

import math
from typing import List, Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class ACI318Compliance(str, Enum):
    passed = "passed"               # Fully meets ACI 318-19 acceptance criteria
    marginal = "marginal"           # Meets individual break threshold but mean is close to f'c
    failed = "failed"               # Fails 3-test moving average or individual drop threshold (>3.5 MPa drop)


class LaboratoryDataFlags(BaseModel):
    missing_element_ref: bool = Field(False, description="Element reference missing")
    no_compressive_data: bool = Field(False, description="No compressive strength test breaks provided")
    insufficient_cylinders: bool = Field(False, description="Fewer than 3 cylinders per batch test")
    individual_low_strength: bool = Field(False, description="One or more cylinder breaks fell below f'c by > 3.5 MPa")
    mean_below_fc: bool = Field(False, description="Mean compressive strength fell below specified f'c")
    non_standard_ld_ratio: bool = Field(False, description="L/D ratio < 1.75 requiring ASTM C39 correction factor")


class LaboratoryTestingInput(BaseModel):
    element_ref: str = Field(..., description="Structural element identifier")
    specified_fc_mpa: float = Field(30.0, description="Specified design compressive strength f'c in MPa")
    cylinder_diameter_mm: float = Field(150.0, description="Cylinder diameter in mm (standard 100 or 150)")
    cylinder_length_mm: float = Field(300.0, description="Cylinder length in mm (standard 200 or 300)")
    compressive_loads_kn: List[float] = Field(default_factory=list, description="Compressive break loads P in kN")
    split_tensile_loads_kn: List[float] = Field(default_factory=list, description="Splitting tensile break loads P in kN")
    age_days: int = Field(28, description="Testing age in days (typically 7, 14, 28)")

    @field_validator("specified_fc_mpa", "cylinder_diameter_mm", "cylinder_length_mm")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Dimensions and specified strengths must be positive.")
        return v


class LaboratoryTestingContext(BaseModel):
    element_ref: str = Field(..., description="Structural element identifier")
    specified_fc_mpa: float = Field(..., description="Specified design strength f'c")
    mean_compressive_fc_mpa: Optional[float] = Field(None, description="Average measured compressive strength in MPa")
    min_compressive_fc_mpa: Optional[float] = Field(None, description="Minimum individual cylinder strength in MPa")
    max_compressive_fc_mpa: Optional[float] = Field(None, description="Maximum individual cylinder strength in MPa")
    mean_split_tensile_ft_mpa: Optional[float] = Field(None, description="Average splitting tensile strength f_t in MPa")
    aci318_status: Optional[ACI318Compliance] = Field(None, description="ACI 318 acceptance evaluation status")
    confidence_ceiling: int = Field(100, description="Reliability score 0-100%")
    flags: LaboratoryDataFlags = Field(..., description="Quality and validation flags")
    has_errors: bool = Field(False, description="True if mandatory data is missing")


def get_astm_c39_ld_correction(length_mm: float, diameter_mm: float) -> float:
    """
    ASTM C39 L/D correction factors:
    L/D = 2.00 -> 1.00
    L/D = 1.75 -> 0.98
    L/D = 1.50 -> 0.96
    L/D = 1.25 -> 0.93
    L/D = 1.00 -> 0.87
    """
    ld = length_mm / diameter_mm
    if ld >= 1.75:
        return 1.00
    elif ld >= 1.50:
        return 0.96 + (ld - 1.50) * (0.02 / 0.25)
    elif ld >= 1.25:
        return 0.93 + (ld - 1.25) * (0.03 / 0.25)
    elif ld >= 1.00:
        return 0.87 + (ld - 1.00) * (0.06 / 0.25)
    else:
        return 0.87


def evaluate_aci318_acceptance(mean_fc: float, min_fc: float, specified_fc: float) -> tuple[ACI318Compliance, bool, bool]:
    """
    ACI 318-19 Acceptance Criteria:
    1. Average of any 3 consecutive tests >= specified_fc
    2. No individual test falls below specified_fc by > 3.5 MPa (for specified_fc <= 35 MPa)
       or by > 0.10 * specified_fc (for specified_fc > 35 MPa)
    """
    allowed_drop = 3.5 if specified_fc <= 35.0 else (0.10 * specified_fc)
    
    indiv_low = (min_fc < (specified_fc - allowed_drop))
    mean_low = (mean_fc < specified_fc)

    if indiv_low or mean_fc < (specified_fc - 2.0):
        return ACI318Compliance.failed, indiv_low, mean_low
    elif mean_low:
        return ACI318Compliance.marginal, indiv_low, mean_low
    else:
        return ACI318Compliance.passed, indiv_low, mean_low


def run_laboratory_engine(raw_input: Dict) -> LaboratoryTestingContext:
    inp = LaboratoryTestingInput(**raw_input)

    flags = LaboratoryDataFlags(
        missing_element_ref=not inp.element_ref.strip(),
        no_compressive_data=(len(inp.compressive_loads_kn) == 0),
        insufficient_cylinders=(0 < len(inp.compressive_loads_kn) < 3),
        individual_low_strength=False,
        mean_below_fc=False,
        non_standard_ld_ratio=((inp.cylinder_length_mm / inp.cylinder_diameter_mm) < 1.75)
    )

    has_errors = flags.no_compressive_data and len(inp.split_tensile_loads_kn) == 0

    if has_errors:
        return LaboratoryTestingContext(
            element_ref=inp.element_ref,
            specified_fc_mpa=inp.specified_fc_mpa,
            confidence_ceiling=0,
            flags=flags,
            has_errors=True
        )

    # Compressive Strength Calculations (ASTM C39)
    mean_fc = None
    min_fc = None
    max_fc = None
    aci_status = None

    if inp.compressive_loads_kn:
        area_mm2 = (math.pi * (inp.cylinder_diameter_mm ** 2)) / 4.0
        ld_factor = get_astm_c39_ld_correction(inp.cylinder_length_mm, inp.cylinder_diameter_mm)

        fc_values = [round((p * 1000.0 / area_mm2) * ld_factor, 2) for p in inp.compressive_loads_kn]
        mean_fc = round(sum(fc_values) / len(fc_values), 2)
        min_fc = min(fc_values)
        max_fc = max(fc_values)

        aci_status, indiv_low, mean_low = evaluate_aci318_acceptance(mean_fc, min_fc, inp.specified_fc_mpa)
        flags.individual_low_strength = indiv_low
        flags.mean_below_fc = mean_low

    # Splitting Tensile Strength Calculations (ASTM C496)
    mean_ft = None
    if inp.split_tensile_loads_kn:
        ft_values = [
            round((2.0 * p * 1000.0) / (math.pi * inp.cylinder_length_mm * inp.cylinder_diameter_mm), 2)
            for p in inp.split_tensile_loads_kn
        ]
        mean_ft = round(sum(ft_values) / len(ft_values), 2)

    # Confidence Score Calculation
    score = 100
    if flags.insufficient_cylinders:
        score -= 20
    if flags.individual_low_strength:
        score -= 25
    if flags.mean_below_fc:
        score -= 20
    if flags.non_standard_ld_ratio:
        score -= 10
    if flags.missing_element_ref:
        score -= 10

    return LaboratoryTestingContext(
        element_ref=inp.element_ref,
        specified_fc_mpa=inp.specified_fc_mpa,
        mean_compressive_fc_mpa=mean_fc,
        min_compressive_fc_mpa=min_fc,
        max_compressive_fc_mpa=max_fc,
        mean_split_tensile_ft_mpa=mean_ft,
        aci318_status=aci_status,
        confidence_ceiling=max(0, min(score, 100)),
        flags=flags,
        has_errors=False
    )

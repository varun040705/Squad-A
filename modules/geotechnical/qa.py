"""
OX1 NDT Platform - Geotechnical QA Module
Squad A - Segment GEO-1: Standard Penetration Test (SPT N60 - ASTM D1586) & Terzaghi Soil Bearing Capacity
"""

import math
from typing import List, Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class FootingShape(str, Enum):
    strip = "strip"
    square = "square"
    circular = "circular"


class SoilDensityClass(str, Enum):
    very_loose = "very_loose"       # N60 < 4
    loose = "loose"                 # 4 - 10
    medium_dense = "medium_dense"   # 10 - 30
    dense = "dense"                 # 30 - 50
    very_dense = "very_dense"       # > 50


class GeotechnicalDataFlags(BaseModel):
    missing_element_ref: bool = Field(False, description="Element reference missing")
    no_spt_data: bool = Field(False, description="No raw SPT N-value provided")
    invalid_soil_params: bool = Field(False, description="Friction angle or unit weight out of physical range")
    low_bearing_capacity: bool = Field(False, description="Allowable bearing capacity < 100 kPa")


class GeotechnicalQAInput(BaseModel):
    element_ref: str = Field(..., description="Structural element identifier")
    raw_spt_n: Optional[int] = Field(None, description="Raw SPT blow count sum of 2nd and 3rd 6-inch increments")
    energy_ratio_ce: float = Field(0.60, description="Hammer energy ratio CE (0.60 safety, 0.80 auto)")
    rod_length_cr: float = Field(0.85, description="Rod length correction factor CR (0.75 - 1.0)")
    sampler_type_cs: float = Field(1.0, description="Sampler liner correction factor CS (1.0 standard, 1.2 no liner)")
    borehole_diam_cb: float = Field(1.0, description="Borehole diameter correction factor CB")
    overburden_cn: float = Field(1.0, description="Overburden pressure correction factor CN")
    footing_width_b_m: float = Field(1.5, description="Footing width B in meters")
    footing_depth_df_m: float = Field(1.0, description="Footing embedment depth Df in meters")
    soil_cohesion_c_kpa: float = Field(10.0, description="Soil cohesion c in kPa")
    soil_friction_phi_deg: float = Field(30.0, description="Soil internal friction angle phi in degrees")
    soil_unit_weight_gamma_kn_m3: float = Field(18.0, description="Soil total unit weight gamma in kN/m3")
    factor_of_safety: float = Field(3.0, description="Design factor of safety FS for allowable capacity")
    footing_shape: FootingShape = Field(FootingShape.square, description="Footing geometry type")

    @field_validator("footing_width_b_m", "footing_depth_df_m", "soil_unit_weight_gamma_kn_m3", "factor_of_safety")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Dimensions, unit weights, and safety factors must be positive.")
        return v


class GeotechnicalQAContext(BaseModel):
    element_ref: str = Field(..., description="Structural element identifier")
    corrected_spt_n60: Optional[float] = Field(None, description="Field energy-corrected N60 value")
    overburden_corrected_n1_60: Optional[float] = Field(None, description="Overburden-normalized (N1)60 value")
    soil_density_class: Optional[SoilDensityClass] = Field(None, description="Soil compactness/consistency rating")
    terzaghi_ult_bearing_kpa: Optional[float] = Field(None, description="Terzaghi ultimate bearing capacity q_ult in kPa")
    allowable_bearing_kpa: Optional[float] = Field(None, description="Allowable bearing capacity q_all in kPa")
    confidence_ceiling: int = Field(100, description="Reliability score 0-100%")
    flags: GeotechnicalDataFlags = Field(..., description="Quality and validation flags")
    has_errors: bool = Field(False, description="True if mandatory data is missing")


def calculate_spt_corrections(
    raw_n: int, ce: float, cr: float, cs: float, cb: float, cn: float
) -> tuple[float, float, SoilDensityClass]:
    """
    N60 = N_raw * (CE * CR * CS * CB) / 0.60
    (N1)60 = N60 * CN
    """
    n60 = round(raw_n * (ce * cr * cs * cb) / 0.60, 1)
    n1_60 = round(n60 * cn, 1)

    if n60 < 4:
        density = SoilDensityClass.very_loose
    elif n60 <= 10:
        density = SoilDensityClass.loose
    elif n60 <= 30:
        density = SoilDensityClass.medium_dense
    elif n60 <= 50:
        density = SoilDensityClass.dense
    else:
        density = SoilDensityClass.very_dense

    return n60, n1_60, density


def calculate_terzaghi_bearing_capacity(
    b_m: float, df_m: float, c_kpa: float, phi_deg: float, gamma_kn_m3: float, fs: float, shape: FootingShape
) -> tuple[float, float]:
    """
    Terzaghi Ultimate Bearing Capacity Equation:
    q_ult = c * Nc * sc + q * Nq + 0.5 * gamma * B * Ngamma * sgamma
    q = gamma * Df
    """
    phi_rad = math.radians(phi_deg)
    q_overburden = gamma_kn_m3 * df_m

    # Terzaghi Bearing Capacity Factors
    if phi_deg == 0:
        nc, nq, ng = 5.7, 1.0, 0.0
    else:
        a = math.exp((0.75 * math.pi - phi_rad / 2.0) * math.tan(phi_rad))
        nq = (a ** 2) / (2.0 * (math.cos(math.radians(45) + phi_rad / 2.0) ** 2))
        nc = (nq - 1.0) / math.tan(phi_rad)
        ng = (2.0 * (nq + 1.0) * math.tan(phi_rad)) / (1.0 + 0.4 * math.sin(4.0 * phi_rad))

    # Shape factors
    if shape == FootingShape.square:
        sc, sg = 1.3, 0.8
    elif shape == FootingShape.circular:
        sc, sg = 1.3, 0.6
    else:
        # Strip footing
        sc, sg = 1.0, 1.0

    q_ult = (c_kpa * nc * sc) + (q_overburden * nq) + (0.5 * gamma_kn_m3 * b_m * ng * sg)
    q_all = q_ult / fs

    return round(q_ult, 1), round(q_all, 1)


def run_geotechnical_engine(raw_input: Dict) -> GeotechnicalQAContext:
    inp = GeotechnicalQAInput(**raw_input)

    flags = GeotechnicalDataFlags(
        missing_element_ref=not inp.element_ref.strip(),
        no_spt_data=(inp.raw_spt_n is None),
        invalid_soil_params=(inp.soil_friction_phi_deg < 0 or inp.soil_friction_phi_deg > 50),
        low_bearing_capacity=False
    )

    has_errors = flags.invalid_soil_params

    if has_errors:
        return GeotechnicalQAContext(
            element_ref=inp.element_ref,
            confidence_ceiling=0,
            flags=flags,
            has_errors=True
        )

    # SPT Corrections
    n60, n1_60, density = None, None, None
    if inp.raw_spt_n is not None:
        n60, n1_60, density = calculate_spt_corrections(
            inp.raw_spt_n, inp.energy_ratio_ce, inp.rod_length_cr,
            inp.sampler_type_cs, inp.borehole_diam_cb, inp.overburden_cn
        )

    # Terzaghi Bearing Capacity
    q_ult, q_all = calculate_terzaghi_bearing_capacity(
        inp.footing_width_b_m, inp.footing_depth_df_m, inp.soil_cohesion_c_kpa,
        inp.soil_friction_phi_deg, inp.soil_unit_weight_gamma_kn_m3, inp.factor_of_safety, inp.footing_shape
    )

    flags.low_bearing_capacity = (q_all < 100.0)

    # Confidence Score Calculation
    score = 100
    if flags.no_spt_data:
        score -= 20
    if flags.low_bearing_capacity:
        score -= 15
    if flags.missing_element_ref:
        score -= 10

    return GeotechnicalQAContext(
        element_ref=inp.element_ref,
        corrected_spt_n60=n60,
        overburden_corrected_n1_60=n1_60,
        soil_density_class=density,
        terzaghi_ult_bearing_kpa=q_ult,
        allowable_bearing_kpa=q_all,
        confidence_ceiling=max(0, min(score, 100)),
        flags=flags,
        has_errors=False
    )

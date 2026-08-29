"""
OX1 NDT Platform - Forensics & Failure Investigation Module
Squad A - Segment FOR-1: Carbonation Depth Rate (dc = k * sqrt(t)) & Chloride Ingress Diffusion (Fick's 2nd Law)
"""

import math
from typing import Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class DepassivationRisk(str, Enum):
    safe = "safe"                   # Service life remaining > 15 years
    warning = "warning"             # Service life remaining 0 - 15 years
    depassivated = "depassivated"   # Carbonation or critical chloride has reached rebar depth


class ForensicsDataFlags(BaseModel):
    missing_element_ref: bool = Field(False, description="Element reference missing")
    no_carbonation_data: bool = Field(False, description="Carbonation depth or age missing")
    no_chloride_data: bool = Field(False, description="Surface chloride or diffusion coefficient missing")
    rebar_depassivated: bool = Field(False, description="Front reached reinforcement cover depth")
    high_carbonation_rate: bool = Field(False, description="Carbonation coefficient k > 4.0 mm/year^0.5")


class ForensicsInvestigationInput(BaseModel):
    element_ref: str = Field(..., description="Structural element identifier")
    service_age_years: float = Field(20.0, description="Current structure age in years")
    cover_depth_mm: float = Field(40.0, description="Clear concrete cover depth to rebar in mm")
    carbonation_depth_mm: Optional[float] = Field(None, description="Measured carbonation front depth in mm")
    surface_chloride_cs_pct: Optional[float] = Field(None, description="Surface chloride concentration Cs (% by weight of concrete)")
    depth_x_mm: Optional[float] = Field(None, description="Target evaluation depth x in mm (defaults to cover depth)")
    diffusion_coeff_d_m2s: Optional[float] = Field(1e-12, description="Chloride diffusion coefficient D in m2/s (e.g. 1e-12)")
    threshold_chloride_ct_pct: float = Field(0.05, description="Critical chloride threshold Ct for corrosion initiation (% by weight)")

    @field_validator("service_age_years", "cover_depth_mm", "threshold_chloride_ct_pct")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Age, cover depth, and thresholds must be positive.")
        return v


class ForensicsInvestigationContext(BaseModel):
    element_ref: str = Field(..., description="Structural element identifier")
    carbonation_coefficient_k: Optional[float] = Field(None, description="Carbonation rate coefficient k in mm/year^0.5")
    time_to_carbonation_depassivation_years: Optional[float] = Field(None, description="Total age when carbonation reaches rebar")
    carbonation_remaining_life_years: Optional[float] = Field(None, description="Remaining years before carbonation depassivation")
    chloride_at_rebar_pct: Optional[float] = Field(None, description="Calculated chloride concentration at rebar depth C(x,t)")
    time_to_chloride_depassivation_years: Optional[float] = Field(None, description="Estimated years to reach threshold Ct at rebar")
    overall_depassivation_status: Optional[DepassivationRisk] = Field(None, description="Combined depassivation threat level")
    confidence_ceiling: int = Field(100, description="Reliability score 0-100%")
    flags: ForensicsDataFlags = Field(..., description="Quality and validation flags")
    has_errors: bool = Field(False, description="True if mandatory data is missing")


def calculate_carbonation_rate(depth_mm: float, age_years: float, cover_mm: float) -> tuple[float, float, float]:
    """
    dc = k * sqrt(t) => k = dc / sqrt(t)
    t_depass = (cover / k)^2
    t_rem = t_depass - age
    """
    k = depth_mm / math.sqrt(age_years)
    t_depass = (cover_mm / k) ** 2 if k > 0 else 999.0
    t_rem = max(0.0, t_depass - age_years)
    return round(k, 2), round(t_depass, 1), round(t_rem, 1)


def calculate_fick_chloride_diffusion(
    cs_pct: float, depth_mm: float, age_years: float, d_m2s: float, ct_pct: float
) -> tuple[float, float]:
    """
    Fick's 2nd Law Solution:
    C(x,t) = Cs * (1 - erf( x_m / (2 * sqrt(D * t_sec)) ))
    t_sec = age_years * 365.25 * 86400
    """
    t_sec = age_years * 365.25 * 86400.0
    x_m = depth_mm / 1000.0

    z = x_m / (2.0 * math.sqrt(d_m2s * t_sec))
    cx_t = cs_pct * (1.0 - math.erf(z))

    # Approximate time to reach Ct: z_crit where 1 - erf(z_crit) = Ct / Cs
    target_erfc = ct_pct / cs_pct
    if target_erfc >= 1.0 or target_erfc <= 0:
        t_crit_years = 999.0
    else:
        # Approximate inverse erfc for critical depth calculation
        # erf(z) = 1 - target_erfc => z = erfinv(1 - target_erfc)
        z_crit = math.sqrt(-math.log(target_erfc)) # Numerical approximation
        t_crit_sec = (x_m / (2.0 * z_crit)) ** 2 / d_m2s
        t_crit_years = t_crit_sec / (365.25 * 86400.0)

    return round(cx_t, 4), round(t_crit_years, 1)


def run_forensics_engine(raw_input: Dict) -> ForensicsInvestigationContext:
    inp = ForensicsInvestigationInput(**raw_input)

    has_carb = (inp.carbonation_depth_mm is not None)
    has_chlor = (inp.surface_chloride_cs_pct is not None and inp.diffusion_coeff_d_m2s is not None)

    flags = ForensicsDataFlags(
        missing_element_ref=not inp.element_ref.strip(),
        no_carbonation_data=not has_carb,
        no_chloride_data=not has_chlor,
        rebar_depassivated=False,
        high_carbonation_rate=False
    )

    has_errors = flags.no_carbonation_data and flags.no_chloride_data

    if has_errors:
        return ForensicsInvestigationContext(
            element_ref=inp.element_ref,
            confidence_ceiling=0,
            flags=flags,
            has_errors=True
        )

    # Carbonation Calculations
    k, t_carb_depass, carb_rem_life = None, None, None
    if has_carb:
        k, t_carb_depass, carb_rem_life = calculate_carbonation_rate(
            inp.carbonation_depth_mm, inp.service_age_years, inp.cover_depth_mm
        )
        flags.high_carbonation_rate = (k > 4.0)
        if inp.carbonation_depth_mm >= inp.cover_depth_mm:
            flags.rebar_depassivated = True

    # Chloride Diffusion Calculations
    target_depth = inp.depth_x_mm if inp.depth_x_mm is not None else inp.cover_depth_mm
    cx_t, t_chlor_depass = None, None
    if has_chlor:
        cx_t, t_chlor_depass = calculate_fick_chloride_diffusion(
            inp.surface_chloride_cs_pct, target_depth, inp.service_age_years,
            inp.diffusion_coeff_d_m2s, inp.threshold_chloride_ct_pct
        )
        if cx_t >= inp.threshold_chloride_ct_pct:
            flags.rebar_depassivated = True

    # Overall Depassivation Risk Status
    status = DepassivationRisk.safe
    if flags.rebar_depassivated or (carb_rem_life is not None and carb_rem_life == 0):
        status = DepassivationRisk.depassivated
    elif (carb_rem_life is not None and carb_rem_life <= 15.0) or (t_chlor_depass is not None and t_chlor_depass <= inp.service_age_years + 15.0):
        status = DepassivationRisk.warning

    # Confidence Score Calculation
    score = 100
    if flags.no_carbonation_data:
        score -= 20
    if flags.no_chloride_data:
        score -= 20
    if flags.high_carbonation_rate:
        score -= 15
    if flags.rebar_depassivated:
        score -= 25
    if flags.missing_element_ref:
        score -= 10

    return ForensicsInvestigationContext(
        element_ref=inp.element_ref,
        carbonation_coefficient_k=k,
        time_to_carbonation_depassivation_years=t_carb_depass,
        carbonation_remaining_life_years=carb_rem_life,
        chloride_at_rebar_pct=cx_t,
        time_to_chloride_depassivation_years=t_chlor_depass,
        overall_depassivation_status=status,
        confidence_ceiling=max(0, min(score, 100)),
        flags=flags,
        has_errors=False
    )

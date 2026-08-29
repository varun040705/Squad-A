"""
OX1 NDT Platform - Structural Health Monitoring (SHM) Module
Squad A - Segment SHM-1: Thermal Differentials (ACI 207.2R) & Elastic Stress-Strain Yield Ratio
"""

import math
from typing import Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class ThermalRiskLevel(str, Enum):
    low = "low"                     # Delta T <= 15 C
    moderate = "moderate"           # 15 C < Delta T <= 20 C (ACI limit)
    high = "high"                   # Delta T > 20 C (Risk of thermal cracking)


class StressYieldStatus(str, Enum):
    safe = "safe"                   # Stress < 60% of yield
    warning = "warning"             # 60% <= Stress <= 85% of yield
    critical = "critical"           # Stress > 85% of yield (Inelastic / Yield risk)


class SHMDataFlags(BaseModel):
    missing_element_ref: bool = Field(False, description="Element reference missing")
    missing_thermal_data: bool = Field(False, description="Core or surface temperature missing")
    missing_strain_data: bool = Field(False, description="Microstrain measurement missing")
    exceeds_thermal_limit: bool = Field(False, description="Thermal differential exceeds ACI 207.2R 20°C limit")
    high_stress_yield_ratio: bool = Field(False, description="Stress exceeds 85% of yield strength")


class SHMMonitoringInput(BaseModel):
    element_ref: str = Field(..., description="Structural element identifier")
    core_temp_c: Optional[float] = Field(None, description="Mass concrete core temperature in °C")
    surface_temp_c: Optional[float] = Field(None, description="Mass concrete surface temperature in °C")
    ambient_temp_c: Optional[float] = Field(None, description="Ambient air temperature in °C")
    measured_microstrain: Optional[float] = Field(None, description="Gauge strain in microstrain (ue)")
    elastic_modulus_gpa: float = Field(30.0, description="Material Modulus of Elasticity E in GPa (e.g. 30 GPa for concrete)")
    yield_strength_mpa: float = Field(400.0, description="Material Yield Strength in MPa (e.g. 400 MPa rebar, 30 MPa concrete)")
    max_allowable_dt_c: float = Field(20.0, description="ACI 207.2R maximum allowable thermal differential limit in °C")

    @field_validator("elastic_modulus_gpa", "yield_strength_mpa", "max_allowable_dt_c")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Material properties and limits must be positive.")
        return v


class SHMMonitoringContext(BaseModel):
    element_ref: str = Field(..., description="Structural element identifier")
    thermal_differential_dt_c: Optional[float] = Field(None, description="Thermal differential Delta T = T_core - T_surface in °C")
    thermal_risk: Optional[ThermalRiskLevel] = Field(None, description="Thermal cracking risk level per ACI 207.2R")
    calculated_stress_mpa: Optional[float] = Field(None, description="Elastic stress sigma = E * strain in MPa")
    yield_ratio_pct: Optional[float] = Field(None, description="Percentage of yield capacity sigma / f_y * 100%")
    yield_status: Optional[StressYieldStatus] = Field(None, description="Structural yield risk status")
    confidence_ceiling: int = Field(100, description="Reliability score 0-100%")
    flags: SHMDataFlags = Field(..., description="Quality and validation flags")
    has_errors: bool = Field(False, description="True if mandatory data is missing")


def calculate_thermal_differential(t_core: float, t_surface: float, max_dt: float) -> tuple[float, ThermalRiskLevel]:
    dt = t_core - t_surface
    if dt <= 15.0:
        risk = ThermalRiskLevel.low
    elif dt <= max_dt:
        risk = ThermalRiskLevel.moderate
    else:
        risk = ThermalRiskLevel.high
    return round(dt, 1), risk


def calculate_elastic_stress(microstrain: float, e_gpa: float, fy_mpa: float) -> tuple[float, float, StressYieldStatus]:
    """
    sigma = E * strain
    E in GPa = E * 10^3 MPa
    strain = microstrain * 10^-6
    sigma (MPa) = E_gpa * 10^3 * microstrain * 10^-6 = E_gpa * microstrain / 1000
    """
    stress_mpa = (e_gpa * microstrain) / 1000.0
    yield_ratio = (abs(stress_mpa) / fy_mpa) * 100.0

    if yield_ratio > 85.0:
        status = StressYieldStatus.critical
    elif yield_ratio >= 60.0:
        status = StressYieldStatus.warning
    else:
        status = StressYieldStatus.safe

    return round(stress_mpa, 2), round(yield_ratio, 1), status


def run_shm_engine(raw_input: Dict) -> SHMMonitoringContext:
    inp = SHMMonitoringInput(**raw_input)

    has_thermal = (inp.core_temp_c is not None and inp.surface_temp_c is not None)
    has_strain = (inp.measured_microstrain is not None)

    flags = SHMDataFlags(
        missing_element_ref=not inp.element_ref.strip(),
        missing_thermal_data=not has_thermal,
        missing_strain_data=not has_strain,
        exceeds_thermal_limit=False,
        high_stress_yield_ratio=False
    )

    has_errors = flags.missing_thermal_data and flags.missing_strain_data

    if has_errors:
        return SHMMonitoringContext(
            element_ref=inp.element_ref,
            confidence_ceiling=0,
            flags=flags,
            has_errors=True
        )

    # Thermal Differential Calculations
    dt, thermal_risk = None, None
    if has_thermal:
        dt, thermal_risk = calculate_thermal_differential(inp.core_temp_c, inp.surface_temp_c, inp.max_allowable_dt_c)
        flags.exceeds_thermal_limit = (dt > inp.max_allowable_dt_c)

    # Stress-Strain Calculations
    stress, yield_pct, yield_status = None, None, None
    if has_strain:
        stress, yield_pct, yield_status = calculate_elastic_stress(
            inp.measured_microstrain, inp.elastic_modulus_gpa, inp.yield_strength_mpa
        )
        flags.high_stress_yield_ratio = (yield_status == StressYieldStatus.critical)

    # Confidence Score Calculation
    score = 100
    if flags.missing_thermal_data:
        score -= 20
    if flags.missing_strain_data:
        score -= 20
    if flags.exceeds_thermal_limit:
        score -= 25
    if flags.high_stress_yield_ratio:
        score -= 25
    if flags.missing_element_ref:
        score -= 10

    return SHMMonitoringContext(
        element_ref=inp.element_ref,
        thermal_differential_dt_c=dt,
        thermal_risk=thermal_risk,
        calculated_stress_mpa=stress,
        yield_ratio_pct=yield_pct,
        yield_status=yield_status,
        confidence_ceiling=max(0, min(score, 100)),
        flags=flags,
        has_errors=False
    )

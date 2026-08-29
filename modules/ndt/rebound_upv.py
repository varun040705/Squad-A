"""
OX1 NDT Platform - NDT Module
Squad A - Segment NDT-1: Rebound Hammer (ASTM C805) & Ultrasonic Pulse Velocity (ASTM C597)
"""

import math
from typing import List, Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class ImpactAngle(str, Enum):
    horizontal = "horizontal"   # 0 degrees
    downward = "downward"       # -90 degrees (vertical down on slab)
    upward = "upward"           # +90 degrees (vertical up on soffit)


class ConcreteQualityClass(str, Enum):
    excellent = "excellent"     # UPV > 4500 m/s
    good = "good"               # 3500 - 4500 m/s
    medium = "medium"           # 3000 - 3500 m/s
    poor = "poor"               # 2000 - 3000 m/s
    very_poor = "very_poor"     # < 2000 m/s


class NDTDataFlags(BaseModel):
    missing_element_ref: bool = Field(False, description="Element reference missing")
    no_rebound_readings: bool = Field(False, description="No rebound hammer readings provided")
    insufficient_rebound_readings: bool = Field(False, description="Fewer than 10 readings per ASTM C805")
    high_outlier_count: bool = Field(False, description="More than 2 readings discarded per ASTM C805 outlier rule")
    missing_upv_data: bool = Field(False, description="UPV distance or transit time missing")
    high_rebound_variance: bool = Field(False, description="Rebound COV > 15%")


class ReboundUPVInput(BaseModel):
    element_ref: str = Field(..., description="Structural element identifier")
    rebound_readings: List[float] = Field(default_factory=list, description="Rebound numbers (R)")
    impact_angle: ImpactAngle = Field(ImpactAngle.horizontal, description="Hammer orientation angle")
    distance_m: Optional[float] = Field(None, description="UPV transducer path length in meters")
    transit_time_us: Optional[float] = Field(None, description="UPV transit time in microseconds (us)")

    @field_validator("rebound_readings")
    @classmethod
    def validate_rebound(cls, v: List[float]) -> List[float]:
        for idx, val in enumerate(v):
            if val < 10 or val > 100:
                raise ValueError(f"Rebound reading at index {idx} ({val}) must be between 10 and 100.")
        return v


class ReboundUPVContext(BaseModel):
    element_ref: str = Field(..., description="Structural element identifier")
    raw_rebound_average: Optional[float] = Field(None, description="Raw average rebound number")
    filtered_rebound_average: Optional[float] = Field(None, description="ASTM C805 outlier-filtered average rebound number")
    discarded_outliers_count: int = Field(0, description="Count of readings discarded per ASTM C805 6-unit rule")
    estimated_fc_mpa: Optional[float] = Field(None, description="Estimated compressive strength f'c in MPa from Rebound Hammer")
    pulse_velocity_m_s: Optional[float] = Field(None, description="Ultrasonic pulse velocity in m/s")
    concrete_quality: Optional[ConcreteQualityClass] = Field(None, description="Concrete quality classification from UPV")
    sonreb_combined_fc_mpa: Optional[float] = Field(None, description="Combined SonReb estimated compressive strength in MPa")
    confidence_ceiling: int = Field(100, description="Reliability score 0-100%")
    flags: NDTDataFlags = Field(..., description="Quality and validation flags")
    has_errors: bool = Field(False, description="True if mandatory data is missing")


def apply_astm_c805_outlier_filter(readings: List[float]) -> tuple[float, List[float], int]:
    """
    ASTM C805 rule: Calculate mean of 10+ readings. Discard any reading that differs
    from the mean by more than 6 units. Re-calculate mean of valid readings.
    """
    if not readings:
        return 0.0, [], 0
    
    initial_mean = sum(readings) / len(readings)
    valid_readings = [r for r in readings if abs(r - initial_mean) <= 6.0]
    discarded_count = len(readings) - len(valid_readings)
    
    if not valid_readings:
        return initial_mean, readings, 0
        
    filtered_mean = sum(valid_readings) / len(valid_readings)
    return round(filtered_mean, 2), valid_readings, discarded_count


def calculate_rebound_fc(r_avg: float, angle: ImpactAngle) -> float:
    """
    Converts rebound number R to compressive strength f'c (MPa) with angle adjustment.
    """
    # Angle adjustment factor: downward reads slightly higher, upward reads slightly lower
    angle_corr = 0.0
    if angle == ImpactAngle.downward:
        angle_corr = -2.5
    elif angle == ImpactAngle.upward:
        angle_corr = +3.0
        
    r_corr = r_avg + angle_corr
    
    # Standard calibration curve: f'c = 0.025 * R^2 + 0.4 * R - 5.0
    fc = 0.025 * (r_corr ** 2) + 0.4 * r_corr - 5.0
    return round(max(fc, 5.0), 2)


def classify_upv_quality(velocity_m_s: float) -> ConcreteQualityClass:
    """
    ASTM C597 Quality Classification based on wave speed (m/s).
    """
    if velocity_m_s > 4500.0:
        return ConcreteQualityClass.excellent
    elif velocity_m_s >= 3500.0:
        return ConcreteQualityClass.good
    elif velocity_m_s >= 3000.0:
        return ConcreteQualityClass.medium
    elif velocity_m_s >= 2000.0:
        return ConcreteQualityClass.poor
    else:
        return ConcreteQualityClass.very_poor


def compute_sonreb_combined_fc(r_avg: float, v_m_s: float) -> float:
    """
    SonReb method (RILEM): Combined Rebound Hammer & UPV estimation.
    f'c = a * (V^b) * (R^c)
    a = 1.2e-9, b = 2.6, c = 1.4
    """
    fc = 1.2e-9 * (v_m_s ** 2.6) * (r_avg ** 1.4)
    return round(fc, 2)


def run_ndt_engine(raw_input: Dict) -> ReboundUPVContext:
    inp = ReboundUPVInput(**raw_input)
    
    flags = NDTDataFlags(
        missing_element_ref=not inp.element_ref.strip(),
        no_rebound_readings=(len(inp.rebound_readings) == 0),
        insufficient_rebound_readings=(0 < len(inp.rebound_readings) < 10),
        high_outlier_count=False,
        missing_upv_data=(inp.distance_m is None or inp.transit_time_us is None or inp.transit_time_us <= 0),
        high_rebound_variance=False
    )
    
    has_errors = flags.no_rebound_readings and flags.missing_upv_data
    
    if has_errors:
        return ReboundUPVContext(
            element_ref=inp.element_ref,
            confidence_ceiling=0,
            flags=flags,
            has_errors=True
        )

    # Rebound Calculations
    raw_avg = sum(inp.rebound_readings) / len(inp.rebound_readings) if inp.rebound_readings else None
    filtered_avg, valid_readings, discarded_count = apply_astm_c805_outlier_filter(inp.rebound_readings) if inp.rebound_readings else (None, [], 0)
    flags.high_outlier_count = (discarded_count > 2)
    
    if valid_readings and len(valid_readings) > 1:
        mean_val = sum(valid_readings) / len(valid_readings)
        var = sum((x - mean_val)**2 for x in valid_readings) / (len(valid_readings) - 1)
        cov = math.sqrt(var) / mean_val if mean_val > 0 else 0
        flags.high_rebound_variance = (cov > 0.15)
        
    estimated_fc = calculate_rebound_fc(filtered_avg, inp.impact_angle) if filtered_avg is not None else None

    # UPV Calculations
    velocity = None
    quality = None
    if inp.distance_m and inp.transit_time_us and inp.transit_time_us > 0:
        velocity = round((inp.distance_m * 1e6) / inp.transit_time_us, 1)
        quality = classify_upv_quality(velocity)

    # SonReb Combined
    sonreb_fc = None
    if filtered_avg is not None and velocity is not None:
        sonreb_fc = compute_sonreb_combined_fc(filtered_avg, velocity)

    # Confidence Score Calculation
    score = 100
    if flags.insufficient_rebound_readings:
        score -= 20
    if flags.high_outlier_count:
        score -= 20
    if flags.high_rebound_variance:
        score -= 15
    if flags.missing_upv_data:
        score -= 15
    if flags.missing_element_ref:
        score -= 10
        
    return ReboundUPVContext(
        element_ref=inp.element_ref,
        raw_rebound_average=round(raw_avg, 2) if raw_avg is not None else None,
        filtered_rebound_average=filtered_avg,
        discarded_outliers_count=discarded_count,
        estimated_fc_mpa=estimated_fc,
        pulse_velocity_m_s=velocity,
        concrete_quality=quality,
        sonreb_combined_fc_mpa=sonreb_fc,
        confidence_ceiling=max(0, min(score, 100)),
        flags=flags,
        has_errors=False
    )

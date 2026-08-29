"""
OX1 NDT Platform - Survey QA Module
Squad A - Segment SURV-1: Verticality / Out-of-Plumbness (ACI 117) & Settlement Monitoring
"""

import math
from typing import List, Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class PlumbnessStatus(str, Enum):
    compliant = "compliant"         # Within ACI 117 tolerance (delta/H <= 1/500)
    warning = "warning"             # 1/500 < delta/H <= 1/300
    non_compliant = "non_compliant" # delta/H > 1/300 or exceeds absolute cap


class SettlementAlertLevel(str, Enum):
    normal = "normal"               # Settlement rate < 1.0 mm/month
    warning = "warning"             # Settlement rate 1.0 - 3.0 mm/month
    critical = "critical"           # Settlement rate > 3.0 mm/month or total > 25 mm


class SurveyDataFlags(BaseModel):
    missing_element_ref: bool = Field(False, description="Element reference missing")
    invalid_height: bool = Field(False, description="Height is missing or zero")
    no_plumbness_data: bool = Field(False, description="Top offsets missing")
    no_settlement_history: bool = Field(False, description="Settlement readings missing")
    exceeds_plumbness_tolerance: bool = Field(False, description="Verticality drift exceeds allowable ACI 117 threshold")
    high_settlement_rate: bool = Field(False, description="Settlement rate exceeds warning limits")


class SettlementRecord(BaseModel):
    day: float = Field(..., description="Observation day count")
    settlement_mm: float = Field(..., description="Measured cumulative settlement in mm")


class SurveyQAInput(BaseModel):
    element_ref: str = Field(..., description="Structural element identifier")
    height_m: float = Field(..., description="Total element height in meters")
    top_offset_x_mm: Optional[float] = Field(None, description="Horizontal top offset X in mm")
    top_offset_y_mm: Optional[float] = Field(None, description="Horizontal top offset Y in mm")
    settlement_history: List[SettlementRecord] = Field(default_factory=list, description="Historical settlement records")

    @field_validator("height_m")
    @classmethod
    def validate_height(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("height_m must be positive.")
        return v


class SurveyQAContext(BaseModel):
    element_ref: str = Field(..., description="Structural element identifier")
    height_m: float = Field(..., description="Total element height in meters")
    resultant_drift_mm: Optional[float] = Field(None, description="Vector magnitude of top offset delta = sqrt(dx^2 + dy^2)")
    drift_ratio: Optional[float] = Field(None, description="Out-of-plumbness ratio delta / (H * 1000)")
    allowable_drift_mm: Optional[float] = Field(None, description="ACI 117 allowable top offset limit in mm")
    plumbness_status: Optional[PlumbnessStatus] = Field(None, description="Verticality compliance status")
    total_settlement_mm: Optional[float] = Field(None, description="Latest total settlement in mm")
    settlement_rate_mm_month: Optional[float] = Field(None, description="Calculated monthly settlement rate")
    settlement_alert: Optional[SettlementAlertLevel] = Field(None, description="Settlement risk alert level")
    confidence_ceiling: int = Field(100, description="Reliability score 0-100%")
    flags: SurveyDataFlags = Field(..., description="Quality and validation flags")
    has_errors: bool = Field(False, description="True if mandatory data is missing")


def calculate_aci117_allowable_drift(height_m: float) -> float:
    """
    ACI 117 Verticality tolerance:
    Allowable drift delta_max = min(H * 1000 / 500, 150.0 mm)
    """
    return round(min((height_m * 1000.0) / 500.0, 150.0), 1)


def evaluate_plumbness(drift_mm: float, allowable_mm: float, height_m: float) -> PlumbnessStatus:
    ratio = drift_mm / (height_m * 1000.0)
    if drift_mm <= allowable_mm and ratio <= (1.0 / 500.0):
        return PlumbnessStatus.compliant
    elif ratio <= (1.0 / 300.0) and drift_mm <= (allowable_mm * 1.5):
        return PlumbnessStatus.warning
    else:
        return PlumbnessStatus.non_compliant


def calculate_settlement_metrics(history: List[SettlementRecord]) -> tuple[Optional[float], Optional[float], Optional[SettlementAlertLevel]]:
    if not history:
        return None, None, None

    sorted_records = sorted(history, key=lambda r: r.day)
    total_settlement = sorted_records[-1].settlement_mm

    rate_monthly = 0.0
    if len(sorted_records) >= 2:
        dt_days = sorted_records[-1].day - sorted_records[0].day
        ds_mm = sorted_records[-1].settlement_mm - sorted_records[0].settlement_mm
        if dt_days > 0:
            rate_daily = ds_mm / dt_days
            rate_monthly = rate_daily * 30.4375

    alert = SettlementAlertLevel.normal
    if total_settlement > 25.0 or rate_monthly > 3.0:
        alert = SettlementAlertLevel.critical
    elif total_settlement > 10.0 or rate_monthly > 1.0:
        alert = SettlementAlertLevel.warning

    return round(total_settlement, 2), round(rate_monthly, 2), alert


def run_survey_engine(raw_input: Dict) -> SurveyQAContext:
    inp = SurveyQAInput(**raw_input)

    has_plumbness = (inp.top_offset_x_mm is not None and inp.top_offset_y_mm is not None)
    has_settlement = len(inp.settlement_history) > 0

    flags = SurveyDataFlags(
        missing_element_ref=not inp.element_ref.strip(),
        invalid_height=(inp.height_m <= 0),
        no_plumbness_data=not has_plumbness,
        no_settlement_history=not has_settlement,
        exceeds_plumbness_tolerance=False,
        high_settlement_rate=False
    )

    has_errors = flags.no_plumbness_data and flags.no_settlement_history

    if has_errors:
        return SurveyQAContext(
            element_ref=inp.element_ref,
            height_m=inp.height_m,
            confidence_ceiling=0,
            flags=flags,
            has_errors=True
        )

    # Verticality Calculations
    drift = None
    drift_ratio = None
    allowable = None
    plumb_status = None
    if has_plumbness:
        drift = math.sqrt(inp.top_offset_x_mm**2 + inp.top_offset_y_mm**2)
        drift_ratio = drift / (inp.height_m * 1000.0)
        allowable = calculate_aci117_allowable_drift(inp.height_m)
        plumb_status = evaluate_plumbness(drift, allowable, inp.height_m)
        flags.exceeds_plumbness_tolerance = (plumb_status == PlumbnessStatus.non_compliant)

    # Settlement Calculations
    total_settlement, rate_monthly, settlement_alert = calculate_settlement_metrics(inp.settlement_history)
    if settlement_alert in (SettlementAlertLevel.warning, SettlementAlertLevel.critical):
        flags.high_settlement_rate = True

    # Confidence Score Calculation
    score = 100
    if flags.no_plumbness_data:
        score -= 20
    if flags.no_settlement_history:
        score -= 20
    if flags.exceeds_plumbness_tolerance:
        score -= 25
    if flags.high_settlement_rate:
        score -= 15
    if flags.missing_element_ref:
        score -= 10

    return SurveyQAContext(
        element_ref=inp.element_ref,
        height_m=inp.height_m,
        resultant_drift_mm=round(drift, 2) if drift is not None else None,
        drift_ratio=round(drift_ratio, 6) if drift_ratio is not None else None,
        allowable_drift_mm=allowable,
        plumbness_status=plumb_status,
        total_settlement_mm=total_settlement,
        settlement_rate_mm_month=rate_monthly,
        settlement_alert=settlement_alert,
        confidence_ceiling=max(0, min(score, 100)),
        flags=flags,
        has_errors=False
    )

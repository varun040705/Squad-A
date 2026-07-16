"""
OX1 NDT Platform - UPV Module
Squad D - Segment D-1: Contractor Performance Tracker

Reads computed UPV results from the database (readings are passed in as
plain data here - this module never calls Squad A or Squad B directly,
per the work plan's Squad D dependency rule).

For each contractor, computes a rolling 3-week mean corrected velocity
across all their pours and compares it against the project's rolling
mean over the same week window.

Alert condition
----------------
A contractor's rolling 3-week mean is more than 8% below the project's
rolling 3-week mean for 2 or more CONSECUTIVE weeks.

Hard rule
---------
Never run with fewer than 20 total readings in the dataset - return an
empty list rather than speculate on thin data.

Sensor Fusion Only
------------------
No Acoustic Emission. No Visual Inspection. No Electrical Surface
Resistivity.
"""

from __future__ import annotations

from statistics import mean
from typing import Dict, List

from pydantic import BaseModel, Field, field_validator


# =====================================================================
# CONSTANTS
# =====================================================================

MIN_TOTAL_READINGS_REQUIRED = 20

ROLLING_WINDOW_WEEKS = 3

DEVIATION_ALERT_THRESHOLD_PCT = -8.0  # more negative = worse than this fires

MIN_CONSECUTIVE_ALERT_WEEKS = 2

CONTRACTOR_ALERT_SEVERITY = "warning"


# =====================================================================
# SCHEMAS
# =====================================================================

class ContractorReading(BaseModel):
    """
    One UPV reading already attributed to a contractor and a project
    week. This is read from the database - it is NOT raw sensor data
    and carries no dependency on Squad A or Squad B.
    """

    contractor_name: str = Field(..., min_length=1)
    project_id: str = Field(..., min_length=1)
    week_number: int = Field(..., ge=1, description="1-indexed project week.")
    corrected_velocity_kmps: float = Field(..., gt=0)

    @field_validator("contractor_name", "project_id")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Value cannot be blank.")
        return v


class ContractorAlert(BaseModel):
    """Alert emitted when a contractor's rolling mean underperforms the project."""

    contractor: str = Field(...)
    rolling_mean_kmps: float = Field(..., gt=0)
    project_mean_kmps: float = Field(..., gt=0)
    deviation_pct: float = Field(...)
    severity: str = Field(...)
    readings_count: int = Field(..., ge=0)


# =====================================================================
# INTERNAL HELPERS
# =====================================================================

def _group_by_contractor(
    readings: List[ContractorReading],
) -> Dict[str, List[ContractorReading]]:
    grouped: Dict[str, List[ContractorReading]] = {}
    for reading in readings:
        grouped.setdefault(reading.contractor_name, []).append(reading)
    return grouped


def _velocities_in_week_window(
    readings: List[ContractorReading],
    end_week: int,
    window_weeks: int = ROLLING_WINDOW_WEEKS,
) -> List[float]:
    """All velocities with week_number in [end_week - window_weeks + 1, end_week]."""
    start_week = end_week - window_weeks + 1
    return [
        reading.corrected_velocity_kmps
        for reading in readings
        if start_week <= reading.week_number <= end_week
    ]


def _rolling_deviation_by_week(
    contractor_readings: List[ContractorReading],
    all_readings: List[ContractorReading],
) -> Dict[int, float]:
    """
    For every week the contractor has readings in, compute the rolling
    3-week deviation of the contractor's mean vs. the project's mean
    over the same week window.
    """
    deviations: Dict[int, float] = {}
    contractor_weeks = sorted({reading.week_number for reading in contractor_readings})

    for week in contractor_weeks:
        contractor_window = _velocities_in_week_window(contractor_readings, week)
        project_window = _velocities_in_week_window(all_readings, week)

        if not contractor_window or not project_window:
            continue

        contractor_mean = mean(contractor_window)
        project_mean = mean(project_window)

        if project_mean == 0:
            continue

        deviation_pct = ((contractor_mean - project_mean) / project_mean) * 100.0
        deviations[week] = deviation_pct

    return deviations


def _find_qualifying_alert_week(deviations: Dict[int, float]) -> int | None:
    """
    Return the last week of the most recent run of
    MIN_CONSECUTIVE_ALERT_WEEKS-or-more consecutive weeks where the
    deviation is at or below DEVIATION_ALERT_THRESHOLD_PCT. Returns
    None if no qualifying run exists.
    """
    weeks_sorted = sorted(deviations.keys())

    run: List[int] = []
    qualifying_run_end: int | None = None

    for week in weeks_sorted:
        is_breaching = deviations[week] <= DEVIATION_ALERT_THRESHOLD_PCT
        is_consecutive = bool(run) and week == run[-1] + 1

        if is_breaching and (not run or is_consecutive):
            run.append(week)
        else:
            run = [week] if is_breaching else []

        if len(run) >= MIN_CONSECUTIVE_ALERT_WEEKS:
            qualifying_run_end = run[-1]

    return qualifying_run_end


# =====================================================================
# PUBLIC ENTRY POINT
# =====================================================================

def compute_contractor_alerts(
    readings: List[ContractorReading],
) -> List[ContractorAlert]:
    """
    Compute contractor performance alerts across the given readings.

    Hard rule: fewer than MIN_TOTAL_READINGS_REQUIRED total readings in
    the dataset returns an empty list - never speculate on thin data.
    """
    if len(readings) < MIN_TOTAL_READINGS_REQUIRED:
        return []

    grouped = _group_by_contractor(readings)
    alerts: List[ContractorAlert] = []

    for contractor_name, contractor_readings in grouped.items():
        deviations = _rolling_deviation_by_week(contractor_readings, readings)
        alert_week = _find_qualifying_alert_week(deviations)

        if alert_week is None:
            continue

        contractor_window = _velocities_in_week_window(contractor_readings, alert_week)
        project_window = _velocities_in_week_window(readings, alert_week)

        rolling_mean = mean(contractor_window)
        project_mean = mean(project_window)
        deviation_pct = deviations[alert_week]

        alerts.append(
            ContractorAlert(
                contractor=contractor_name,
                rolling_mean_kmps=round(rolling_mean, 2),
                project_mean_kmps=round(project_mean, 2),
                deviation_pct=round(deviation_pct, 1),
                severity=CONTRACTOR_ALERT_SEVERITY,
                readings_count=len(contractor_readings),
            )
        )

    return alerts


# =====================================================================
# PUBLIC EXPORTS
# =====================================================================

__all__ = [
    "ContractorReading",
    "ContractorAlert",
    "compute_contractor_alerts",
]
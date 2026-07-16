"""
OX1 NDT Platform - UPV Module
Squad D - Segment D-2: Element Deterioration Tracker

Reads computed UPV results from the database (visit records passed in
as plain data here - this module never calls Squad A or Squad B
directly, per the work plan's Squad D dependency rule).

For elements with 3 or more separate site visits, computes a simple
linear regression of corrected velocity over elapsed time and flags
elements that are trending down fast enough to warrant priority
inspection.

Flag condition
--------------
Regression slope steeper (more negative) than -0.1 km/s per month
-> flag for priority inspection on the next visit.

Hard rule
---------
Never run with fewer than 3 visits for an element - elements with
fewer than 3 visits are simply excluded from consideration, never
estimated.

Sensor Fusion Only
------------------
No Acoustic Emission. No Visual Inspection. No Electrical Surface
Resistivity.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# =====================================================================
# CONSTANTS
# =====================================================================

MIN_VISITS_REQUIRED = 3

DETERIORATION_SLOPE_THRESHOLD_KMPS_PER_MONTH = -0.1

DETERIORATION_TREND_LABEL = "declining"

DETERIORATION_PRIORITY_LABEL = "inspect_next_visit"


# =====================================================================
# SCHEMAS
# =====================================================================

class ElementVisit(BaseModel):
    """
    One site-visit UPV record for an element, read from the database.
    """

    element_ref: str = Field(..., min_length=1)
    visit_month: float = Field(
        ..., ge=0, description="Elapsed months since the element's first recorded visit."
    )
    corrected_velocity_kmps: float = Field(..., gt=0)

    @field_validator("element_ref")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("element_ref cannot be blank.")
        return v


class ElementDeteriorationFlag(BaseModel):
    """Flag emitted for an element whose velocity is declining too fast."""

    element_ref: str = Field(...)
    slope_kmps_per_month: float = Field(...)
    assessment_count: int = Field(..., ge=MIN_VISITS_REQUIRED)
    trend: str = Field(...)
    priority: str = Field(...)


# =====================================================================
# INTERNAL HELPERS
# =====================================================================

def _group_by_element(visits: List[ElementVisit]) -> Dict[str, List[ElementVisit]]:
    grouped: Dict[str, List[ElementVisit]] = {}
    for visit in visits:
        grouped.setdefault(visit.element_ref, []).append(visit)
    return grouped


def _linear_regression_slope(visits: List[ElementVisit]) -> Optional[float]:
    """
    Ordinary least-squares slope of corrected_velocity_kmps against
    visit_month.

    Returns None if the visits share the same visit_month (a slope is
    not meaningful - never invent a trend from constant-time data).
    """
    x_values = [visit.visit_month for visit in visits]
    y_values = [visit.corrected_velocity_kmps for visit in visits]

    n = len(visits)
    mean_x = sum(x_values) / n
    mean_y = sum(y_values) / n

    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
    denominator = sum((x - mean_x) ** 2 for x in x_values)

    if denominator == 0:
        return None

    return numerator / denominator


# =====================================================================
# PUBLIC ENTRY POINT
# =====================================================================

def compute_deterioration_flags(
    visits: List[ElementVisit],
) -> List[ElementDeteriorationFlag]:
    """
    Compute element deterioration flags across the given visit records.

    Hard rule: elements with fewer than MIN_VISITS_REQUIRED visits are
    excluded from consideration entirely - never estimated on thin data.
    """
    grouped = _group_by_element(visits)
    flags: List[ElementDeteriorationFlag] = []

    for element_ref, element_visits in grouped.items():
        if len(element_visits) < MIN_VISITS_REQUIRED:
            continue

        slope = _linear_regression_slope(element_visits)
        if slope is None:
            continue

        if slope > DETERIORATION_SLOPE_THRESHOLD_KMPS_PER_MONTH:
            continue  # not declining fast enough to warrant a flag

        flags.append(
            ElementDeteriorationFlag(
                element_ref=element_ref,
                slope_kmps_per_month=round(slope, 3),
                assessment_count=len(element_visits),
                trend=DETERIORATION_TREND_LABEL,
                priority=DETERIORATION_PRIORITY_LABEL,
            )
        )

    return flags


# =====================================================================
# PUBLIC EXPORTS
# =====================================================================

__all__ = [
    "ElementVisit",
    "ElementDeteriorationFlag",
    "compute_deterioration_flags",
]
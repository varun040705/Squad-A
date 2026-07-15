"""
OX1 NDT Platform - UPV Module
Squad B - Segment B3: Statistical Defect Detectors

This module implements statistical defect detectors used in the
Sensor Fusion pipeline.

Implemented detectors
---------------------
1. Segregation
2. Excess Water
3. Inadequate Curing

Sensor Fusion Only
------------------
- No Acoustic Emission
- No Visual Inspection
- No Electrical Surface Resistivity
"""

from __future__ import annotations

from statistics import mean
from statistics import pstdev
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from modules.upv.b1_point_level_detectors import (
    GridPoint,
    VelocityGrid,
)


# ============================================================
# CONSTANTS
# ============================================================

SEGREGATION_STD_THRESHOLD = 0.45

EXCESS_WATER_MEAN_THRESHOLD = 3.20

INADEQUATE_CURING_MEAN_THRESHOLD = 3.40


# ============================================================
# RESPONSE MODEL
# ============================================================


class StatisticalDetectionResult(BaseModel):
    """
    Statistical detector response.
    """

    primary_defect: str = Field(...)

    confidence: float = Field(
        ...,
        ge=0,
        le=100,
    )

    reason: str = Field(...)


# ============================================================
# SHARED HELPERS
# ============================================================


def _velocities(
    grid: VelocityGrid,
) -> List[float]:
    """
    Returns all corrected UPV velocities.
    """

    return [
        point.velocity_kmps
        for point in grid.points
    ]


def _mean_velocity(
    grid: VelocityGrid,
) -> float:

    return mean(_velocities(grid))


def _std_velocity(
    grid: VelocityGrid,
) -> float:

    values = _velocities(grid)

    if len(values) <= 1:
        return 0.0

    return pstdev(values)

# ============================================================
# SEGREGATION DETECTOR
# ============================================================

def detect_segregation(
    grid: VelocityGrid,
) -> Optional[StatisticalDetectionResult]:
    """
    Detects segregation.

    Rule
    ----
    Large statistical variation in corrected UPV velocity
    indicates possible aggregate segregation.
    """

    std = _std_velocity(grid)

    if std < SEGREGATION_STD_THRESHOLD:
        return None

    return StatisticalDetectionResult(
        primary_defect="segregation",
        confidence=91.0,
        reason=(
            f"Velocity standard deviation "
            f"({std:.2f} km/s) exceeds the "
            "acceptable segregation threshold."
        ),
    )


# ============================================================
# EXCESS WATER DETECTOR
# ============================================================

def detect_excess_water(
    grid: VelocityGrid,
) -> Optional[StatisticalDetectionResult]:
    """
    Detects excess water.

    Rule
    ----
    A significantly reduced mean velocity across the
    inspection region may indicate excess water in
    the concrete mix.
    """

    average = _mean_velocity(grid)

    if average >= EXCESS_WATER_MEAN_THRESHOLD:
        return None

    return StatisticalDetectionResult(
        primary_defect="excess_water",
        confidence=90.0,
        reason=(
            f"Average UPV velocity "
            f"({average:.2f} km/s) is below "
            "the acceptable limit."
        ),
    )

# ============================================================
# INADEQUATE CURING DETECTOR
# ============================================================

def detect_inadequate_curing(
    grid: VelocityGrid,
) -> Optional[StatisticalDetectionResult]:
    """
    Detects inadequate curing.

    Rule
    ----
    A moderately reduced average UPV velocity may indicate
    insufficient curing of the concrete element.
    """

    average = _mean_velocity(grid)

    if average >= INADEQUATE_CURING_MEAN_THRESHOLD:
        return None

    return StatisticalDetectionResult(
        primary_defect="inadequate_curing",
        confidence=89.0,
        reason=(
            f"Average UPV velocity "
            f"({average:.2f} km/s) indicates "
            "possible inadequate curing."
        ),
    )


# ============================================================
# DETECTOR ORCHESTRATOR
# ============================================================

def run_statistical_detectors(
    grid: VelocityGrid,
) -> Optional[StatisticalDetectionResult]:
    """
    Executes all statistical detectors.

    Priority
    --------
    1. Segregation
    2. Excess Water
    3. Inadequate Curing
    """

    detectors = (
        detect_segregation,
        detect_excess_water,
        detect_inadequate_curing,
    )

    for detector in detectors:

        result = detector(grid)

        if result is not None:
            return result

    return None


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "StatisticalDetectionResult",
    "detect_segregation",
    "detect_excess_water",
    "detect_inadequate_curing",
    "run_statistical_detectors",
]
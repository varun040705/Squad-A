"""
OX1 NDT Platform - UPV Module
Squad B - Segment B-2: Area Level Defect Detectors

This module implements the second stage of the Sensor Fusion
pipeline.

Implemented detectors
---------------------
1. Honeycombing
2. Poor Compaction
3. Cold Joint

This module builds upon the validated point-level data generated
during B1.

Sensor Fusion Only
------------------
- No Acoustic Emission
- No Visual Inspection
- No Electrical Surface Resistivity
"""

from __future__ import annotations

from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

from pydantic import BaseModel
from pydantic import Field

from modules.upv.b1_point_level_detectors import (
    CRACK_THRESHOLD_KMPS,
    GridPoint,
    VelocityGrid,
    build_grid_lookup,
    get_neighbours,
)


# ============================================================
# CONSTANTS
# ============================================================

HONEYCOMB_CLUSTER_SIZE = 4

POOR_COMPACTION_CLUSTER_SIZE = 5

COLD_JOINT_ROW_PERCENTAGE = 0.70

LOW_VELOCITY_LIMIT = 3.0


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================


class AreaDetectionResult(BaseModel):
    """
    Response returned by every area-level detector.
    """

    primary_defect: str = Field(
        ...,
        description="Detected defect."
    )

    point_ids: List[str] = Field(
        default_factory=list,
        description="Affected points."
    )

    confidence: float = Field(
        ...,
        ge=0,
        le=100,
    )

    reason: str = Field(
        ...,
        description="Explanation."
    )


# ============================================================
# SHARED HELPERS
# ============================================================


def _connected_component(
    start: GridPoint,
    lookup: Dict[Tuple[int, int], GridPoint],
) -> List[GridPoint]:
    """
    Returns one connected low-velocity region using DFS.
    """

    visited: Set[str] = set()

    stack: List[GridPoint] = [start]

    component: List[GridPoint] = []

    while stack:

        point = stack.pop()

        if point.point_id in visited:
            continue

        visited.add(point.point_id)

        component.append(point)

        neighbours = get_neighbours(
            lookup,
            point.row,
            point.column,
        )

        for neighbour in neighbours:

            if neighbour.velocity_kmps >= LOW_VELOCITY_LIMIT:
                continue

            if neighbour.point_id in visited:
                continue

            stack.append(neighbour)

    return component


def _all_low_velocity_components(
    grid: VelocityGrid,
) -> List[List[GridPoint]]:
    """
    Finds every connected low-velocity cluster.
    """

    lookup = build_grid_lookup(grid)

    processed: Set[str] = set()

    components: List[List[GridPoint]] = []

    for point in grid.points:

        if point.velocity_kmps >= LOW_VELOCITY_LIMIT:
            continue

        if point.point_id in processed:
            continue

        component = _connected_component(
            point,
            lookup,
        )

        for item in component:
            processed.add(item.point_id)

        components.append(component)

    return components
# ============================================================
# HONEYCOMB DETECTOR
# ============================================================

def detect_honeycombing(
    grid: VelocityGrid,
) -> Optional[AreaDetectionResult]:
    """
    Detects honeycombing.

    Rule
    ----
    Four or more connected low-velocity points indicate a
    localized honeycombed region.
    """

    components = _all_low_velocity_components(grid)

    for component in components:

        if len(component) < HONEYCOMB_CLUSTER_SIZE:
            continue

        return AreaDetectionResult(
            primary_defect="honeycombing",
            point_ids=[
                point.point_id
                for point in component
            ],
            confidence=94.0,
            reason=(
                f"Connected cluster containing "
                f"{len(component)} low-velocity points."
            ),
        )

    return None


# ============================================================
# POOR COMPACTION DETECTOR
# ============================================================

def detect_poor_compaction(
    grid: VelocityGrid,
) -> Optional[AreaDetectionResult]:
    """
    Detects poor compaction.

    Rule
    ----
    Five or more connected low-velocity points indicate
    poor concrete compaction.
    """

    components = _all_low_velocity_components(grid)

    for component in components:

        if len(component) < POOR_COMPACTION_CLUSTER_SIZE:
            continue

        average_velocity = (
            sum(
                point.velocity_kmps
                for point in component
            )
            / len(component)
        )

        return AreaDetectionResult(
            primary_defect="poor_compaction",
            point_ids=[
                point.point_id
                for point in component
            ],
            confidence=96.0,
            reason=(
                f"Cluster average velocity "
                f"{average_velocity:.2f} km/s "
                "indicates poor compaction."
            ),
        )

    return None

# ============================================================
# COLD JOINT DETECTOR
# ============================================================

def detect_cold_joint(
    grid: VelocityGrid,
) -> Optional[AreaDetectionResult]:
    """
    Detects a cold joint.

    Rule
    ----
    If 70% or more of the points in any row have
    velocity below the configured limit, that row
    is classified as a potential cold joint.
    """

    rows = sorted(
        {
            point.row
            for point in grid.points
        }
    )

    for row in rows:

        row_points = [
            point
            for point in grid.points
            if point.row == row
        ]

        if not row_points:
            continue

        low_velocity_points = [
            point
            for point in row_points
            if point.velocity_kmps < LOW_VELOCITY_LIMIT
        ]

        ratio = (
            len(low_velocity_points)
            / len(row_points)
        )

        if ratio < COLD_JOINT_ROW_PERCENTAGE:
            continue

        return AreaDetectionResult(
            primary_defect="cold_joint",
            point_ids=[
                point.point_id
                for point in low_velocity_points
            ],
            confidence=93.0,
            reason=(
                f"{ratio:.0%} of row {row} "
                "contains low-velocity readings."
            ),
        )

    return None


# ============================================================
# DETECTOR ORCHESTRATOR
# ============================================================

def run_area_level_detectors(
    grid: VelocityGrid,
) -> Optional[AreaDetectionResult]:
    """
    Executes all area-level detectors in priority order.

    Priority
    --------
    1. Poor Compaction
    2. Honeycombing
    3. Cold Joint
    """

    detectors = (
        detect_poor_compaction,
        detect_honeycombing,
        detect_cold_joint,
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
    "AreaDetectionResult",
    "detect_honeycombing",
    "detect_poor_compaction",
    "detect_cold_joint",
    "run_area_level_detectors",
]
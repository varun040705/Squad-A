"""
OX1 NDT Platform - UPV Module
Squad B - Segment B-1: Point Level Defect Detectors

This module implements the first stage of the Sensor Fusion defect
analysis pipeline.

Implemented detectors
---------------------
1. Void Detector
2. Crack Detector

The module operates on the context object produced by Squad A and
analyses a velocity grid without using any external AI service.

Workplan Compliance
-------------------
- Sensor Fusion only
- No Acoustic Emission
- No Visual Inspection
- No Electrical Surface Resistivity
- Pydantic v2
- Fully typed
- Pure composable detector functions
"""

from __future__ import annotations

from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Iterable
from typing import Set
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

import math


# ============================================================
# CONSTANTS
# ============================================================

CRACK_THRESHOLD_KMPS = 3.0

VOID_Z_SCORE_THRESHOLD = 3.0

ORTHOGONAL_DIRECTIONS = (
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1),
)

MIN_CRACK_POINTS = 3


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================


class GridPoint(BaseModel):
    """
    Represents one UPV test point.
    """

    point_id: str = Field(
        ...,
        description="Unique point identifier such as P1"
    )

    row: int = Field(
        ...,
        ge=0,
        description="Grid row"
    )

    column: int = Field(
        ...,
        ge=0,
        description="Grid column"
    )

    velocity_kmps: float = Field(
        ...,
        gt=0,
        description="Corrected velocity from Squad A"
    )

    @field_validator("point_id")
    @classmethod
    def validate_point(cls, value: str) -> str:

        value = value.strip().upper()

        if not value.startswith("P"):
            raise ValueError(
                "Point ID must start with 'P'."
            )

        return value


class VelocityGrid(BaseModel):
    """
    Collection of validated test points.
    """

    element_id: UUID

    points: List[GridPoint]

    @field_validator("points")
    @classmethod
    def validate_points(
        cls,
        value: List[GridPoint]
    ) -> List[GridPoint]:

        if len(value) == 0:
            raise ValueError(
                "Velocity grid cannot be empty."
            )

        coordinates = set()

        for point in value:

            coordinate = (
                point.row,
                point.column,
            )

            if coordinate in coordinates:
                raise ValueError(
                    "Duplicate grid coordinate detected."
                )

            coordinates.add(coordinate)

        return value


class DetectionResult(BaseModel):
    """
    Generic detector response.
    """

    primary_defect: str

    point_ids: List[str]

    confidence: float

    reason: str


# ============================================================
# GRID UTILITIES
# ============================================================


def build_grid_lookup(
    grid: VelocityGrid,
) -> Dict[Tuple[int, int], GridPoint]:
    """
    Builds coordinate lookup for O(1) neighbour access.
    """

    return {
        (
            point.row,
            point.column,
        ): point
        for point in grid.points
    }


def get_neighbours(
    lookup: Dict[Tuple[int, int], GridPoint],
    row: int,
    column: int,
) -> List[GridPoint]:
    """
    Returns orthogonal neighbours.
    """

    neighbours: List[GridPoint] = []

    for dr, dc in ORTHOGONAL_DIRECTIONS:

        neighbour = lookup.get(
            (
                row + dr,
                column + dc,
            )
        )

        if neighbour is not None:
            neighbours.append(neighbour)

    return neighbours


def calculate_mean(
    values: Iterable[float],
) -> float:

    values = list(values)

    return sum(values) / len(values)


def calculate_std(
    values: Iterable[float],
) -> float:

    values = list(values)

    mean = calculate_mean(values)

    variance = (
        sum(
            (
                value - mean
            ) ** 2
            for value in values
        )
        / len(values)
    )

    return math.sqrt(variance)


def calculate_z_score(
    value: float,
    mean: float,
    std: float,
) -> float:

    if std == 0:
        return 0.0

    return abs(
        (value - mean) / std
    )
# ============================================================
# VOID DETECTOR
# ============================================================

def detect_void(
    grid: VelocityGrid,
) -> Optional[DetectionResult]:
    """
    Detects an isolated void.

    Rule (AI Work Plan)
    -------------------
    • Z-score > 3
    • No neighbouring point is also below the crack threshold
    """

    lookup = build_grid_lookup(grid)

    velocities = [
        point.velocity_kmps
        for point in grid.points
    ]

    mean = calculate_mean(velocities)
    std = calculate_std(velocities)

    for point in grid.points:

        z_score = calculate_z_score(
            point.velocity_kmps,
            mean,
            std,
        )

        if (
            z_score <= VOID_Z_SCORE_THRESHOLD
            and point.velocity_kmps >= 2.5
        ):
            continue

        neighbours = get_neighbours(
            lookup,
            point.row,
            point.column,
        )

        low_velocity_neighbours = [
            neighbour
            for neighbour in neighbours
            if neighbour.velocity_kmps < CRACK_THRESHOLD_KMPS
        ]

        if len(low_velocity_neighbours) != 0:
            continue

        return DetectionResult(
            primary_defect="void",
            point_ids=[point.point_id],
            confidence=95.0,
            reason=(
                f"{point.point_id} has "
                f"Z-score {z_score:.2f} "
                "with healthy surrounding neighbours."
            ),
        )

    return None


# ============================================================
# CRACK DETECTOR HELPERS
# ============================================================

def _scan_horizontal(
    lookup: Dict[Tuple[int, int], GridPoint],
    rows: List[int],
    columns: List[int],
) -> Optional[List[str]]:
    """
    Scan every row for consecutive low-velocity points.
    """

    for row in rows:

        consecutive: List[str] = []

        for column in columns:

            point = lookup.get((row, column))

            if point is None:

                consecutive.clear()

                continue

            if point.velocity_kmps < CRACK_THRESHOLD_KMPS:

                consecutive.append(point.point_id)

                if len(consecutive) >= MIN_CRACK_POINTS:
                    return consecutive.copy()

            else:

                consecutive.clear()

    return None


def _scan_vertical(
    lookup: Dict[Tuple[int, int], GridPoint],
    rows: List[int],
    columns: List[int],
) -> Optional[List[str]]:
    """
    Scan every column for consecutive low-velocity points.
    """

    for column in columns:

        consecutive: List[str] = []

        for row in rows:

            point = lookup.get((row, column))

            if point is None:

                consecutive.clear()

                continue

            if point.velocity_kmps < CRACK_THRESHOLD_KMPS:

                consecutive.append(point.point_id)

                if len(consecutive) >= MIN_CRACK_POINTS:
                    return consecutive.copy()

            else:

                consecutive.clear()

    return None


def _grid_dimensions(
    grid: VelocityGrid,
) -> Tuple[List[int], List[int]]:
    """
    Returns sorted row and column indexes.
    """

    rows = sorted(
        {
            point.row
            for point in grid.points
        }
    )

    columns = sorted(
        {
            point.column
            for point in grid.points
        }
    )

    return rows, columns

# ============================================================
# CRACK DETECTOR
# ============================================================

def detect_crack(
    grid: VelocityGrid,
) -> Optional[DetectionResult]:
    """
    Detects a crack represented by three or more consecutive
    low-velocity points.

    Work Plan Rule
    --------------
    Three or more consecutive points in a straight line
    with velocity below 3.0 km/s.
    """

    lookup = build_grid_lookup(grid)

    rows, columns = _grid_dimensions(grid)

    horizontal = _scan_horizontal(
        lookup,
        rows,
        columns,
    )

    if horizontal is not None:

        return DetectionResult(
            primary_defect="crack",
            point_ids=horizontal,
            confidence=92.0,
            reason=(
                "Three or more consecutive low-velocity "
                "points detected horizontally."
            ),
        )

    vertical = _scan_vertical(
        lookup,
        rows,
        columns,
    )

    if vertical is not None:

        return DetectionResult(
            primary_defect="crack",
            point_ids=vertical,
            confidence=92.0,
            reason=(
                "Three or more consecutive low-velocity "
                "points detected vertically."
            ),
        )

    return None


# ============================================================
# DETECTOR ORCHESTRATION
# ============================================================

def run_point_level_detectors(
    grid: VelocityGrid,
) -> Optional[DetectionResult]:
    """
    Executes all point-level detectors in priority order.

    Priority
    --------
    1. Void
    2. Crack

    Returns the first matching detector result.
    """

    detectors = (
        detect_void,
        detect_crack,
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
    "GridPoint",
    "VelocityGrid",
    "DetectionResult",
    "detect_void",
    "detect_crack",
    "run_point_level_detectors",
]

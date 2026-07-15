"""
Pytest suite for Squad B - Segment B1

Tests:
- Void detection
- Crack detection (horizontal)
- Crack detection (vertical)
- No defect
- Validation checks
"""

from uuid import uuid4

import pytest

from modules.upv.b1_point_level_detectors import (
    GridPoint,
    VelocityGrid,
    detect_void,
    detect_crack,
    run_point_level_detectors,
)


# ==========================================================
# HELPERS
# ==========================================================


def make_grid(points):
    return VelocityGrid(
        element_id=uuid4(),
        points=points,
    )


# ==========================================================
# VOID DETECTION
# ==========================================================


def test_detect_void():

    grid = make_grid(
        [
            GridPoint(point_id="P1", row=0, column=0, velocity_kmps=4.1),
            GridPoint(point_id="P2", row=0, column=1, velocity_kmps=4.2),
            GridPoint(point_id="P3", row=0, column=2, velocity_kmps=4.0),

            GridPoint(point_id="P4", row=1, column=0, velocity_kmps=4.1),
            GridPoint(point_id="P5", row=1, column=1, velocity_kmps=1.2),
            GridPoint(point_id="P6", row=1, column=2, velocity_kmps=4.2),

            GridPoint(point_id="P7", row=2, column=0, velocity_kmps=4.3),
            GridPoint(point_id="P8", row=2, column=1, velocity_kmps=4.2),
            GridPoint(point_id="P9", row=2, column=2, velocity_kmps=4.1),
        ]
    )

    result = detect_void(grid)

    assert result is not None
    assert result.primary_defect == "void"
    assert result.point_ids == ["P5"]


# ==========================================================
# HORIZONTAL CRACK
# ==========================================================


def test_detect_horizontal_crack():

    grid = make_grid(
        [
            GridPoint(point_id="P1", row=0, column=0, velocity_kmps=4.2),
            GridPoint(point_id="P2", row=0, column=1, velocity_kmps=4.1),
            GridPoint(point_id="P3", row=0, column=2, velocity_kmps=4.0),

            GridPoint(point_id="P4", row=1, column=0, velocity_kmps=2.7),
            GridPoint(point_id="P5", row=1, column=1, velocity_kmps=2.8),
            GridPoint(point_id="P6", row=1, column=2, velocity_kmps=2.6),

            GridPoint(point_id="P7", row=2, column=0, velocity_kmps=4.2),
            GridPoint(point_id="P8", row=2, column=1, velocity_kmps=4.0),
            GridPoint(point_id="P9", row=2, column=2, velocity_kmps=4.1),
        ]
    )

    result = detect_crack(grid)

    assert result is not None
    assert result.primary_defect == "crack"
    assert result.point_ids == ["P4", "P5", "P6"]


# ==========================================================
# VERTICAL CRACK
# ==========================================================


def test_detect_vertical_crack():

    grid = make_grid(
        [
            GridPoint(point_id="P1", row=0, column=0, velocity_kmps=4.2),
            GridPoint(point_id="P2", row=0, column=1, velocity_kmps=2.8),
            GridPoint(point_id="P3", row=0, column=2, velocity_kmps=4.0),

            GridPoint(point_id="P4", row=1, column=0, velocity_kmps=4.2),
            GridPoint(point_id="P5", row=1, column=1, velocity_kmps=2.7),
            GridPoint(point_id="P6", row=1, column=2, velocity_kmps=4.1),

            GridPoint(point_id="P7", row=2, column=0, velocity_kmps=4.3),
            GridPoint(point_id="P8", row=2, column=1, velocity_kmps=2.6),
            GridPoint(point_id="P9", row=2, column=2, velocity_kmps=4.2),
        ]
    )

    result = detect_crack(grid)

    assert result is not None
    assert result.primary_defect == "crack"
    assert result.point_ids == ["P2", "P5", "P8"]


# ==========================================================
# NO DEFECT
# ==========================================================


def test_no_defect():

    grid = make_grid(
        [
            GridPoint(point_id="P1", row=0, column=0, velocity_kmps=4.0),
            GridPoint(point_id="P2", row=0, column=1, velocity_kmps=4.1),
            GridPoint(point_id="P3", row=0, column=2, velocity_kmps=4.2),

            GridPoint(point_id="P4", row=1, column=0, velocity_kmps=4.1),
            GridPoint(point_id="P5", row=1, column=1, velocity_kmps=4.0),
            GridPoint(point_id="P6", row=1, column=2, velocity_kmps=4.2),

            GridPoint(point_id="P7", row=2, column=0, velocity_kmps=4.1),
            GridPoint(point_id="P8", row=2, column=1, velocity_kmps=4.0),
            GridPoint(point_id="P9", row=2, column=2, velocity_kmps=4.1),
        ]
    )

    assert detect_void(grid) is None
    assert detect_crack(grid) is None
    assert run_point_level_detectors(grid) is None


# ==========================================================
# DUPLICATE COORDINATE VALIDATION
# ==========================================================


def test_duplicate_coordinate():

    with pytest.raises(ValueError):

        VelocityGrid(
            element_id=uuid4(),
            points=[
                GridPoint(
                    point_id="P1",
                    row=0,
                    column=0,
                    velocity_kmps=4.0,
                ),
                GridPoint(
                    point_id="P2",
                    row=0,
                    column=0,
                    velocity_kmps=4.1,
                ),
            ],
        )


# ==========================================================
# INVALID POINT ID
# ==========================================================


def test_invalid_point_id():

    with pytest.raises(ValueError):

        GridPoint(
            point_id="1",
            row=0,
            column=0,
            velocity_kmps=4.0,
        )


# ==========================================================
# EMPTY GRID
# ==========================================================


def test_empty_grid():

    with pytest.raises(ValueError):

        VelocityGrid(
            element_id=uuid4(),
            points=[],
        )
"""
Pytest suite for Squad B - Segment B3

Tests:
- Segregation detection
- Excess water detection
- Inadequate curing detection
- No statistical defect
- Orchestrator priority
"""

from uuid import uuid4

from modules.upv.b1_point_level_detectors import (
    GridPoint,
    VelocityGrid,
)

from modules.upv.b3_statistical_detectors import (
    detect_segregation,
    detect_excess_water,
    detect_inadequate_curing,
    run_statistical_detectors,
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
# SEGREGATION
# ==========================================================


def test_detect_segregation():

    grid = make_grid(
        [
            GridPoint(point_id="P1", row=0, column=0, velocity_kmps=2.1),
            GridPoint(point_id="P2", row=0, column=1, velocity_kmps=4.5),
            GridPoint(point_id="P3", row=1, column=0, velocity_kmps=2.3),
            GridPoint(point_id="P4", row=1, column=1, velocity_kmps=4.6),
            GridPoint(point_id="P5", row=2, column=0, velocity_kmps=2.2),
            GridPoint(point_id="P6", row=2, column=1, velocity_kmps=4.4),
        ]
    )

    result = detect_segregation(grid)

    assert result is not None
    assert result.primary_defect == "segregation"


# ==========================================================
# EXCESS WATER
# ==========================================================


def test_detect_excess_water():

    grid = make_grid(
        [
            GridPoint(point_id="P1", row=0, column=0, velocity_kmps=3.0),
            GridPoint(point_id="P2", row=0, column=1, velocity_kmps=3.1),
            GridPoint(point_id="P3", row=1, column=0, velocity_kmps=3.2),
            GridPoint(point_id="P4", row=1, column=1, velocity_kmps=3.0),
        ]
    )

    result = detect_excess_water(grid)

    assert result is not None
    assert result.primary_defect == "excess_water"


# ==========================================================
# INADEQUATE CURING
# ==========================================================


def test_detect_inadequate_curing():

    grid = make_grid(
        [
            GridPoint(point_id="P1", row=0, column=0, velocity_kmps=3.3),
            GridPoint(point_id="P2", row=0, column=1, velocity_kmps=3.4),
            GridPoint(point_id="P3", row=1, column=0, velocity_kmps=3.3),
            GridPoint(point_id="P4", row=1, column=1, velocity_kmps=3.4),
        ]
    )

    result = detect_inadequate_curing(grid)

    assert result is not None
    assert result.primary_defect == "inadequate_curing"


# ==========================================================
# NO STATISTICAL DEFECT
# ==========================================================


def test_no_statistical_defect():

    grid = make_grid(
        [
            GridPoint(point_id="P1", row=0, column=0, velocity_kmps=4.2),
            GridPoint(point_id="P2", row=0, column=1, velocity_kmps=4.1),
            GridPoint(point_id="P3", row=1, column=0, velocity_kmps=4.2),
            GridPoint(point_id="P4", row=1, column=1, velocity_kmps=4.3),
        ]
    )

    assert detect_segregation(grid) is None
    assert detect_excess_water(grid) is None
    assert detect_inadequate_curing(grid) is None
    assert run_statistical_detectors(grid) is None


# ==========================================================
# ORCHESTRATOR PRIORITY
# ==========================================================


def test_orchestrator_priority():

    grid = make_grid(
        [
            GridPoint(point_id="P1", row=0, column=0, velocity_kmps=2.0),
            GridPoint(point_id="P2", row=0, column=1, velocity_kmps=4.6),
            GridPoint(point_id="P3", row=1, column=0, velocity_kmps=2.2),
            GridPoint(point_id="P4", row=1, column=1, velocity_kmps=4.7),
            GridPoint(point_id="P5", row=2, column=0, velocity_kmps=2.1),
            GridPoint(point_id="P6", row=2, column=1, velocity_kmps=4.5),
        ]
    )

    result = run_statistical_detectors(grid)

    assert result is not None
    assert result.primary_defect == "segregation"
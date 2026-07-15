"""
Pytest suite for Squad B - Segment B2

Tests:
- Honeycombing detection
- Poor compaction detection
- Cold joint detection
- No defect
- Orchestrator priority
"""

from uuid import uuid4

from modules.upv.b1_point_level_detectors import (
    GridPoint,
    VelocityGrid,
)

from modules.upv.b2_area_level_detectors import (
    detect_honeycombing,
    detect_poor_compaction,
    detect_cold_joint,
    run_area_level_detectors,
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
# HONEYCOMBING
# ==========================================================


def test_detect_honeycombing():

    grid = make_grid(
        [
            GridPoint(point_id="P1", row=0, column=0, velocity_kmps=2.7),
            GridPoint(point_id="P2", row=0, column=1, velocity_kmps=2.8),

            GridPoint(point_id="P3", row=1, column=0, velocity_kmps=2.9),
            GridPoint(point_id="P4", row=1, column=1, velocity_kmps=2.6),

            GridPoint(point_id="P5", row=2, column=2, velocity_kmps=4.2),
        ]
    )

    result = detect_honeycombing(grid)

    assert result is not None
    assert result.primary_defect == "honeycombing"
    assert len(result.point_ids) == 4


# ==========================================================
# POOR COMPACTION
# ==========================================================


def test_detect_poor_compaction():

    grid = make_grid(
        [
            GridPoint(point_id="P1", row=0, column=0, velocity_kmps=2.6),
            GridPoint(point_id="P2", row=0, column=1, velocity_kmps=2.7),

            GridPoint(point_id="P3", row=1, column=0, velocity_kmps=2.8),
            GridPoint(point_id="P4", row=1, column=1, velocity_kmps=2.9),

            GridPoint(point_id="P5", row=2, column=0, velocity_kmps=2.7),

            GridPoint(point_id="P6", row=3, column=3, velocity_kmps=4.2),
        ]
    )

    result = detect_poor_compaction(grid)

    assert result is not None
    assert result.primary_defect == "poor_compaction"
    assert len(result.point_ids) == 5


# ==========================================================
# COLD JOINT
# ==========================================================


def test_detect_cold_joint():

    grid = make_grid(
        [
            GridPoint(point_id="P1", row=0, column=0, velocity_kmps=2.7),
            GridPoint(point_id="P2", row=0, column=1, velocity_kmps=2.8),
            GridPoint(point_id="P3", row=0, column=2, velocity_kmps=2.6),
            GridPoint(point_id="P4", row=0, column=3, velocity_kmps=4.2),

            GridPoint(point_id="P5", row=1, column=0, velocity_kmps=4.2),
            GridPoint(point_id="P6", row=1, column=1, velocity_kmps=4.1),
        ]
    )

    result = detect_cold_joint(grid)

    assert result is not None
    assert result.primary_defect == "cold_joint"
    assert len(result.point_ids) == 3


# ==========================================================
# NO DEFECT
# ==========================================================


def test_no_area_level_defect():

    grid = make_grid(
        [
            GridPoint(point_id="P1", row=0, column=0, velocity_kmps=4.2),
            GridPoint(point_id="P2", row=0, column=1, velocity_kmps=4.1),

            GridPoint(point_id="P3", row=1, column=0, velocity_kmps=4.2),
            GridPoint(point_id="P4", row=1, column=1, velocity_kmps=4.0),
        ]
    )

    assert detect_honeycombing(grid) is None
    assert detect_poor_compaction(grid) is None
    assert detect_cold_joint(grid) is None
    assert run_area_level_detectors(grid) is None


# ==========================================================
# ORCHESTRATOR PRIORITY
# ==========================================================


def test_orchestrator_priority():

    grid = make_grid(
        [
            GridPoint(point_id="P1", row=0, column=0, velocity_kmps=2.6),
            GridPoint(point_id="P2", row=0, column=1, velocity_kmps=2.7),

            GridPoint(point_id="P3", row=1, column=0, velocity_kmps=2.8),
            GridPoint(point_id="P4", row=1, column=1, velocity_kmps=2.7),

            GridPoint(point_id="P5", row=2, column=0, velocity_kmps=2.9),

            GridPoint(point_id="P6", row=3, column=3, velocity_kmps=4.2),
        ]
    )

    result = run_area_level_detectors(grid)

    assert result is not None
    assert result.primary_defect == "poor_compaction"
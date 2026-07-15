"""
test_h3.py
"""
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from squad_h.models import (
    LocalizationResult,
    TrendResult,
    LoadHistoryResult,
    H2Result,
    TrendType,
)

from squad_h.ae_h3 import build_context


def test_context_builder_grade_undetermined_when_no_load_history():
    # No felicity_ratio/calm_ratio available -> grade must stay None and
    # be flagged, never fabricated (not even a "safe" IV default).

    h2 = H2Result(

        localization=LocalizationResult(
            success=False,
            x=None,
            y=None,
            z=None,
            sensors_used=1,
            message="insufficient_sensors_for_localization",
        ),

        trend=TrendResult(
            b_value=None,
            trend=TrendType.INSUFFICIENT_DATA,
            confidence=0,
        ),

        load_history=LoadHistoryResult(),

        total_hits=2,
        eligible_hits=1,
        flags=["insufficient_sensors_for_localization"],
    )

    context = build_context(
        "AE-001",
        "C-07",
        h2,
    )

    assert context.inspection_id == "AE-001"
    assert context.element_ref == "C-07"
    assert context.hits_total == 2
    assert context.grade is None
    assert "grade_undetermined" in context.flags
    assert context.hits_localized == 0


def test_context_builder_grades_when_felicity_available():

    h2 = H2Result(

        localization=LocalizationResult(
            success=True, x=1.0, y=1.0, z=0.0, sensors_used=4,
            message="Localization successful",
        ),

        trend=TrendResult(b_value=1.1, trend=TrendType.STABLE, confidence=70),

        load_history=LoadHistoryResult(
            felicity_ratio=0.82, calm_ratio=0.1,
            previous_peak_load=100.0, current_peak_load=120.0,
        ),

        total_hits=214,
        eligible_hits=189,
    )

    context = build_context("AE-002", "C-08", h2)

    assert context.grade.value == "III"   # 0.80 <= 0.82 < 0.95
    assert context.felicity_ratio == 0.82
    assert context.hits_localized == 189


if __name__ == "__main__":
    test_context_builder_grade_undetermined_when_no_load_history()
    test_context_builder_grades_when_felicity_available()
    print("✓ test_h3 passed")
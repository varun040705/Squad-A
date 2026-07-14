"""
test_grade_engine.py
"""

from squad_h.models import (
    LocalizationResult,
    TrendResult,
    LoadHistoryResult,
    H2Result,
    TrendType,
    AEGrade,
)

from squad_h.grade_engine import determine_grade


def test_grade_is_iv_when_localization_fails():

    h2 = H2Result(

        localization=LocalizationResult(
            success=False,
            x=None,
            y=None,
            z=None,
            sensors_used=1,
            message="Failed",
        ),

        trend=TrendResult(
            b_value=None,
            trend=TrendType.INSUFFICIENT_DATA,
            confidence=0,
        ),

        load_history=LoadHistoryResult(),

        total_hits=2,
        eligible_hits=1,
    )

    grade = determine_grade(h2)

    assert grade == AEGrade.IV
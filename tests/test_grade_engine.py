"""
test_grade_engine.py
"""
import pytest

from squad_h.models import (
    LocalizationResult,
    TrendResult,
    LoadHistoryResult,
    H2Result,
    TrendType,
    AEGrade,
)

from squad_h.grade_engine import determine_grade


def _make_h2(felicity_ratio=None, calm_ratio=None, localization_success=True):
    return H2Result(
        localization=LocalizationResult(
            success=localization_success,
            x=0.0 if localization_success else None,
            y=0.0 if localization_success else None,
            z=0.0 if localization_success else None,
            sensors_used=4 if localization_success else 1,
            message="Localization successful" if localization_success else "insufficient_sensors_for_localization",
        ),
        trend=TrendResult(b_value=1.1, trend=TrendType.STABLE, confidence=70),
        load_history=LoadHistoryResult(felicity_ratio=felicity_ratio, calm_ratio=calm_ratio),
        total_hits=2,
        eligible_hits=1,
    )


def test_grade_raises_when_no_load_history_at_all():
    # Never estimate -- if we truly have nothing to grade on, raise
    # rather than default to some grade.

    h2 = _make_h2(felicity_ratio=None, calm_ratio=None)

    with pytest.raises(ValueError):
        determine_grade(h2)


def test_grade_i_when_felicity_ratio_is_full_kaiser():

    h2 = _make_h2(felicity_ratio=1.0, calm_ratio=0.05)
    assert determine_grade(h2) == AEGrade.I


def test_grade_ii_for_minor_felicity_effect():

    h2 = _make_h2(felicity_ratio=0.97, calm_ratio=0.05)
    assert determine_grade(h2) == AEGrade.II


def test_grade_iii_for_moderate_felicity_effect():

    h2 = _make_h2(felicity_ratio=0.82, calm_ratio=0.05)
    assert determine_grade(h2) == AEGrade.III


def test_grade_iv_for_severe_felicity_effect():

    h2 = _make_h2(felicity_ratio=0.5, calm_ratio=0.05)
    assert determine_grade(h2) == AEGrade.IV


def test_grade_iv_forced_by_high_calm_ratio_regardless_of_felicity():
    # High calm_ratio overrides an otherwise-healthy Felicity ratio.

    h2 = _make_h2(felicity_ratio=1.0, calm_ratio=0.5)
    assert determine_grade(h2) == AEGrade.IV


def test_grade_is_independent_of_localization_success():
    # Localization failure is a separate flag, not a grading input --
    # a hit that fails to localize can still carry a valid Felicity ratio.

    h2 = _make_h2(felicity_ratio=0.97, calm_ratio=0.05, localization_success=False)
    assert determine_grade(h2) == AEGrade.II
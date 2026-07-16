"""
tests/test_d2_element_deterioration_tracker.py

Unit tests for Segment D-2: element deterioration tracker.

No AI call and no dependency on Squad A or Squad B here - all tests
build synthetic ElementVisit data directly, matching how this module
reads pre-computed results from the database.
"""

from __future__ import annotations

import pytest

from modules.upv.d2_element_deterioration_tracker import (
    DETERIORATION_PRIORITY_LABEL,
    DETERIORATION_TREND_LABEL,
    MIN_VISITS_REQUIRED,
    ElementDeteriorationFlag,
    ElementVisit,
    compute_deterioration_flags,
)


def _visit(element_ref: str, visit_month: float, velocity: float) -> ElementVisit:
    return ElementVisit(
        element_ref=element_ref,
        visit_month=visit_month,
        corrected_velocity_kmps=velocity,
    )


class TestElementVisitModel:
    def test_valid_visit_constructs(self) -> None:
        visit = _visit("C-07", 0, 4.2)
        assert visit.element_ref == "C-07"

    def test_rejects_non_positive_velocity(self) -> None:
        with pytest.raises(Exception):
            ElementVisit(element_ref="C-07", visit_month=0, corrected_velocity_kmps=0)

    def test_rejects_blank_element_ref(self) -> None:
        with pytest.raises(Exception):
            ElementVisit(element_ref="   ", visit_month=0, corrected_velocity_kmps=4.0)

    def test_rejects_negative_visit_month(self) -> None:
        with pytest.raises(Exception):
            ElementVisit(element_ref="C-07", visit_month=-1, corrected_velocity_kmps=4.0)


class TestComputeDeteriorationFlags:
    def test_declining_element_with_three_visits_is_flagged(self) -> None:
        """
        Acceptance case: element with 3 visits at 4.2, 4.0, 3.85 km/s
        (months 0, 1, 2) -> declining slope, flag generated.
        """
        visits = [
            _visit("C-07", 0, 4.2),
            _visit("C-07", 1, 4.0),
            _visit("C-07", 2, 3.85),
        ]

        flags = compute_deterioration_flags(visits)

        assert len(flags) == 1
        flag = flags[0]
        assert isinstance(flag, ElementDeteriorationFlag)
        assert flag.element_ref == "C-07"
        assert flag.slope_kmps_per_month == pytest.approx(-0.175, abs=1e-3)
        assert flag.assessment_count == 3
        assert flag.trend == DETERIORATION_TREND_LABEL
        assert flag.priority == DETERIORATION_PRIORITY_LABEL

    def test_element_with_only_two_visits_returns_empty_array(self) -> None:
        visits = [
            _visit("C-08", 0, 4.2),
            _visit("C-08", 1, 4.0),
        ]
        assert compute_deterioration_flags(visits) == []

    def test_stable_element_is_not_flagged(self) -> None:
        visits = [
            _visit("C-09", 0, 4.0),
            _visit("C-09", 1, 4.0),
            _visit("C-09", 2, 4.0),
        ]
        assert compute_deterioration_flags(visits) == []

    def test_improving_element_is_not_flagged(self) -> None:
        visits = [
            _visit("C-10", 0, 3.5),
            _visit("C-10", 1, 3.8),
            _visit("C-10", 2, 4.1),
        ]
        assert compute_deterioration_flags(visits) == []

    def test_mild_decline_below_threshold_is_not_flagged(self) -> None:
        """Slope of exactly -0.05 km/s/month is not steeper than -0.1, so no flag."""
        visits = [
            _visit("C-11", 0, 4.10),
            _visit("C-11", 1, 4.05),
            _visit("C-11", 2, 4.00),
        ]
        flags = compute_deterioration_flags(visits)
        assert flags == []

    def test_multiple_elements_only_declining_ones_flagged(self) -> None:
        visits = [
            _visit("C-07", 0, 4.2),
            _visit("C-07", 1, 4.0),
            _visit("C-07", 2, 3.85),
            _visit("C-09", 0, 4.0),
            _visit("C-09", 1, 4.0),
            _visit("C-09", 2, 4.0),
        ]
        flags = compute_deterioration_flags(visits)
        flagged_refs = {f.element_ref for f in flags}
        assert flagged_refs == {"C-07"}

    def test_element_with_identical_visit_months_is_not_flagged(self) -> None:
        """No time variance -> slope is undefined, never invent a trend."""
        visits = [
            _visit("C-12", 0, 4.2),
            _visit("C-12", 0, 4.0),
            _visit("C-12", 0, 3.8),
        ]
        assert compute_deterioration_flags(visits) == []

    def test_four_visits_still_evaluated_correctly(self) -> None:
        visits = [
            _visit("C-13", 0, 4.4),
            _visit("C-13", 1, 4.2),
            _visit("C-13", 2, 4.0),
            _visit("C-13", 3, 3.8),
        ]
        flags = compute_deterioration_flags(visits)
        assert len(flags) == 1
        assert flags[0].assessment_count == 4
        assert flags[0].slope_kmps_per_month == pytest.approx(-0.2, abs=1e-3)


class TestHardRuleMinimumVisits:
    def test_min_visits_constant_is_three(self) -> None:
        assert MIN_VISITS_REQUIRED == 3

    def test_single_visit_element_excluded(self) -> None:
        visits = [_visit("C-14", 0, 3.0)]
        assert compute_deterioration_flags(visits) == []

    def test_no_visits_returns_empty_array(self) -> None:
        assert compute_deterioration_flags([]) == []
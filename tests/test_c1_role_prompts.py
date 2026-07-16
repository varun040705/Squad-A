"""
tests/test_c1_role_prompts.py

Unit tests for Segment C-1: the three analytical role prompts.

No live Anthropic API calls are made. Every test injects a FakeClaudeClient
that returns canned JSON text, matching the `ClaudeMessageClient` Protocol
that production code depends on.
"""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from modules.upv.b1_point_level_detectors import GridPoint, VelocityGrid
from modules.upv.squad_a_context_engine import FinalContextObject
from modules.upv.c1_role_prompts import (
    ClaudeResponseParsingError,
    HistoricalVisit,
    RecommendedAction,
    RoleResult,
    build_historical_comparator_prompt,
    build_is_code_checker_prompt,
    build_spatial_analyst_prompt,
    run_historical_comparator_role,
    run_is_code_checker_role,
    run_spatial_analyst_role,
)


class FakeClaudeClient:
    """Test double satisfying the ClaudeMessageClient protocol."""

    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.last_system_prompt: str | None = None
        self.last_user_prompt: str | None = None
        self.call_count = 0

    def create_message(self, *, system_prompt: str, user_prompt: str) -> str:
        self.call_count += 1
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        return self.response_text


def _valid_role_json(
    primary_defect: str = "void",
    flag_score: int = 70,
    recommended_action: str = "monitor",
    reasoning: str = "P5 recorded 2.4 km/s against a healthy grid.",
) -> str:
    return json.dumps(
        {
            "primary_defect": primary_defect,
            "flag_score": flag_score,
            "recommended_action": recommended_action,
            "reasoning": reasoning,
        }
    )


def _sample_grid() -> VelocityGrid:
    return VelocityGrid(
        element_id=uuid4(),
        points=[
            GridPoint(point_id="P1", row=0, column=0, velocity_kmps=4.0),
            GridPoint(point_id="P2", row=0, column=1, velocity_kmps=4.1),
            GridPoint(point_id="P3", row=1, column=0, velocity_kmps=2.4),
            GridPoint(point_id="P4", row=1, column=1, velocity_kmps=3.9),
        ],
    )


def _sample_context() -> FinalContextObject:
    return FinalContextObject(
        element_id=uuid4(),
        element_type="column",
        raw_velocity_kmps=4.1,
        corrected_velocity_kmps=3.6,
        corrections_applied=[],
        effective_bands={"excellent": 4.5, "good": 3.5, "medium": 3.0, "poor": 2.9},
        age_mismatch_index=0.95,
        confidence_ceiling=95,
        flags=[],
    )


# --------------------------------------------------------------------------
# Role 1 - IS Code Checker
# --------------------------------------------------------------------------

class TestIsCodeCheckerRole:
    def test_returns_valid_role_result(self) -> None:
        context = _sample_context()
        grid = _sample_grid()
        client = FakeClaudeClient(_valid_role_json())

        result = run_is_code_checker_role(context, grid, client=client)

        assert isinstance(result, RoleResult)
        assert result.primary_defect == "void"
        assert result.flag_score == 70
        assert result.recommended_action == RecommendedAction.MONITOR
        assert client.call_count == 1

    def test_prompt_includes_effective_bands_and_point_velocities(self) -> None:
        context = _sample_context()
        grid = _sample_grid()
        prompt = build_is_code_checker_prompt(context, grid)

        assert "P3" in prompt
        assert "2.400" in prompt
        assert "excellent" in prompt

    def test_system_prompt_forbids_hedging_and_mpa(self) -> None:
        context = _sample_context()
        grid = _sample_grid()
        client = FakeClaudeClient(_valid_role_json())

        run_is_code_checker_role(context, grid, client=client)

        system_prompt_lower = client.last_system_prompt.lower()
        assert "mpa" in system_prompt_lower  # rule text mentions it explicitly
        assert "hedging" in system_prompt_lower

    def test_raises_on_malformed_json(self) -> None:
        context = _sample_context()
        grid = _sample_grid()
        client = FakeClaudeClient("not valid json at all")

        with pytest.raises(ClaudeResponseParsingError):
            run_is_code_checker_role(context, grid, client=client)

    def test_raises_when_required_field_missing(self) -> None:
        context = _sample_context()
        grid = _sample_grid()
        incomplete = json.dumps({"primary_defect": "void", "flag_score": 50})
        client = FakeClaudeClient(incomplete)

        with pytest.raises(ClaudeResponseParsingError):
            run_is_code_checker_role(context, grid, client=client)

    def test_strips_markdown_fences_before_parsing(self) -> None:
        context = _sample_context()
        grid = _sample_grid()
        fenced = f"```json\n{_valid_role_json()}\n```"
        client = FakeClaudeClient(fenced)

        result = run_is_code_checker_role(context, grid, client=client)
        assert result.primary_defect == "void"


# --------------------------------------------------------------------------
# Role 2 - Spatial Analyst
# --------------------------------------------------------------------------

class TestSpatialAnalystRole:
    def test_returns_valid_role_result(self) -> None:
        grid = _sample_grid()
        client = FakeClaudeClient(
            _valid_role_json(primary_defect="crack", flag_score=60, recommended_action="retest")
        )

        result = run_spatial_analyst_role(grid, client=client)

        assert result.primary_defect == "crack"
        assert result.recommended_action == RecommendedAction.RETEST

    def test_prompt_includes_grid_coordinates_not_bands(self) -> None:
        grid = _sample_grid()
        prompt = build_spatial_analyst_prompt(grid)

        assert "row=1" in prompt
        assert "column=1" in prompt
        assert "excellent" not in prompt  # no IS band language leaks in

    def test_system_prompt_explicitly_excludes_is_thresholds(self) -> None:
        grid = _sample_grid()
        client = FakeClaudeClient(_valid_role_json())

        run_spatial_analyst_role(grid, client=client)

        assert "IS 13311" in client.last_system_prompt


# --------------------------------------------------------------------------
# Role 3 - Historical Comparator
# --------------------------------------------------------------------------

class TestHistoricalComparatorRole:
    def test_returns_none_with_zero_prior_visits(self) -> None:
        client = FakeClaudeClient(_valid_role_json())
        result = run_historical_comparator_role(3.6, [], client=client)

        assert result is None
        assert client.call_count == 0

    def test_returns_none_with_only_one_prior_visit(self) -> None:
        client = FakeClaudeClient(_valid_role_json())
        visits = [HistoricalVisit(visit_sequence=1, corrected_velocity_kmps=4.0)]

        result = run_historical_comparator_role(3.6, visits, client=client)

        assert result is None
        assert client.call_count == 0

    def test_activates_with_two_prior_visits(self) -> None:
        client = FakeClaudeClient(
            _valid_role_json(primary_defect="deterioration", recommended_action="escalate")
        )
        visits = [
            HistoricalVisit(visit_sequence=1, corrected_velocity_kmps=4.2),
            HistoricalVisit(visit_sequence=2, corrected_velocity_kmps=4.0),
        ]

        result = run_historical_comparator_role(3.6, visits, client=client)

        assert result is not None
        assert result.primary_defect == "deterioration"
        assert result.recommended_action == RecommendedAction.ESCALATE
        assert client.call_count == 1

    def test_prompt_lists_visits_in_sequence_order(self) -> None:
        visits = [
            HistoricalVisit(visit_sequence=2, corrected_velocity_kmps=4.0),
            HistoricalVisit(visit_sequence=1, corrected_velocity_kmps=4.2),
        ]
        prompt = build_historical_comparator_prompt(3.6, visits)

        first_index = prompt.index("Visit 1")
        second_index = prompt.index("Visit 2")
        assert first_index < second_index


# --------------------------------------------------------------------------
# Cross-role output hygiene
# --------------------------------------------------------------------------

class TestOutputHygiene:
    def test_role_result_rejects_out_of_range_flag_score(self) -> None:
        with pytest.raises(Exception):
            RoleResult(
                primary_defect="void",
                flag_score=150,
                recommended_action="monitor",
                reasoning="test",
            )

    def test_role_result_rejects_invalid_recommended_action(self) -> None:
        with pytest.raises(Exception):
            RoleResult(
                primary_defect="void",
                flag_score=50,
                recommended_action="do_nothing",
                reasoning="test",
            )

    def test_role_result_rejects_empty_primary_defect(self) -> None:
        with pytest.raises(Exception):
            RoleResult(
                primary_defect="   ",
                flag_score=50,
                recommended_action="monitor",
                reasoning="test",
            )
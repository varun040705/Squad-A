"""
tests/test_c2_resolverlgic_consenusoutput.py

Unit tests for Segment C-2: resolver logic & consensus output.

`resolve_roles` is pure Python (no AI call) and is tested directly.
`run_consensus_pipeline` wiring is tested with FakeClaudeClient doubles
injected per role - no live Anthropic API calls are made anywhere here.
"""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from modules.upv.b1_point_level_detectors import GridPoint, VelocityGrid
from modules.upv.squad_a_context_engine import FinalContextObject
from modules.upv.c1_role_prompts import HistoricalVisit, RecommendedAction, RoleResult
from modules.upv.c2_resolverlogic_consenusoutput import (
    ConsensusConfidence,
    ConsensusResult,
    resolve_roles,
    run_consensus_pipeline,
)


class FakeClaudeClient:
    """Test double satisfying the ClaudeMessageClient protocol."""

    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.call_count = 0

    def create_message(self, *, system_prompt: str, user_prompt: str) -> str:
        self.call_count += 1
        return self.response_text


def _role(
    primary_defect: str,
    flag_score: int,
    recommended_action: str,
    reasoning: str = "P5 recorded an anomalous drop against neighbouring points.",
) -> RoleResult:
    return RoleResult(
        primary_defect=primary_defect,
        flag_score=flag_score,
        recommended_action=recommended_action,
        reasoning=reasoning,
    )


def _role_json(
    primary_defect: str,
    flag_score: int,
    recommended_action: str,
    reasoning: str = "P5 recorded an anomalous drop against neighbouring points.",
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
# resolve_roles - 3-role acceptance scenarios (from the work plan)
# --------------------------------------------------------------------------

class TestResolveRolesThreeRoleAgreement:
    def test_all_three_agree_on_void_is_high_confidence(self) -> None:
        r1 = _role("void", 90, "escalate")
        r2 = _role("void", 85, "escalate")
        r3 = _role("void", 88, "escalate")

        result = resolve_roles(r1, r2, r3)

        assert result.primary_defect == "void"
        assert result.confidence == ConsensusConfidence.HIGH
        assert result.roles_agreed == 3
        assert result.total_roles_considered == 3
        assert result.recommended_action == RecommendedAction.ESCALATE

    def test_two_agree_on_honeycombing_one_says_void_is_medium(self) -> None:
        r1 = _role("honeycombing", 80, "flag_for_review")
        r2 = _role("honeycombing", 75, "monitor")
        r3 = _role("void", 60, "monitor")

        result = resolve_roles(r1, r2, r3)

        assert result.primary_defect == "honeycombing"
        assert result.confidence == ConsensusConfidence.MEDIUM
        assert result.roles_agreed == 2
        assert result.total_roles_considered == 3

    def test_all_three_disagree_is_uncertain_low_flag_for_review(self) -> None:
        r1 = _role("void", 70, "monitor")
        r2 = _role("crack", 65, "monitor")
        r3 = _role("segregation", 60, "monitor")

        result = resolve_roles(r1, r2, r3)

        assert result.primary_defect == "uncertain"
        assert result.confidence == ConsensusConfidence.LOW
        assert result.recommended_action == RecommendedAction.FLAG_FOR_REVIEW
        assert result.roles_agreed == 1
        assert result.total_roles_considered == 3

    def test_final_action_is_always_most_severe_never_downgraded(self) -> None:
        r1 = _role("void", 90, "escalate")
        r2 = _role("void", 40, "monitor")
        r3 = _role("void", 50, "monitor")

        result = resolve_roles(r1, r2, r3)

        assert result.recommended_action == RecommendedAction.ESCALATE

    def test_flag_score_uses_reference_weighted_blend_for_three_roles(self) -> None:
        r1 = _role("void", 90, "monitor")
        r2 = _role("void", 80, "monitor")
        r3 = _role("void", 70, "monitor")

        result = resolve_roles(r1, r2, r3)

        expected = round(90 * 0.33 + 80 * 0.33 + 70 * 0.34)
        assert result.flag_score == expected


# --------------------------------------------------------------------------
# resolve_roles - 2-role fallback (Historical Comparator unavailable)
# --------------------------------------------------------------------------

class TestResolveRolesTwoRoleFallback:
    def test_two_roles_agree_is_medium_confidence(self) -> None:
        r1 = _role("crack", 70, "retest")
        r2 = _role("crack", 65, "monitor")

        result = resolve_roles(r1, r2, role_3_result=None)

        assert result.primary_defect == "crack"
        assert result.confidence == ConsensusConfidence.MEDIUM
        assert result.roles_agreed == 2
        assert result.total_roles_considered == 2
        assert result.recommended_action == RecommendedAction.RETEST

    def test_two_roles_disagree_is_uncertain_low_flag_for_review(self) -> None:
        r1 = _role("void", 70, "monitor")
        r2 = _role("crack", 65, "monitor")

        result = resolve_roles(r1, r2, role_3_result=None)

        assert result.primary_defect == "uncertain"
        assert result.confidence == ConsensusConfidence.LOW
        assert result.recommended_action == RecommendedAction.FLAG_FOR_REVIEW
        assert result.roles_agreed == 1
        assert result.total_roles_considered == 2

    def test_flag_score_uses_equal_weight_mean_for_two_roles(self) -> None:
        r1 = _role("crack", 80, "monitor")
        r2 = _role("crack", 60, "monitor")

        result = resolve_roles(r1, r2, role_3_result=None)

        assert result.flag_score == round((80 + 60) / 2)


# --------------------------------------------------------------------------
# ConsensusResult schema validation
# --------------------------------------------------------------------------

class TestConsensusResultSchema:
    def test_rejects_out_of_range_flag_score(self) -> None:
        with pytest.raises(Exception):
            ConsensusResult(
                primary_defect="void",
                flag_score=101,
                confidence="high",
                recommended_action="escalate",
                roles_agreed=3,
                total_roles_considered=3,
            )

    def test_rejects_total_roles_considered_outside_two_or_three(self) -> None:
        with pytest.raises(Exception):
            ConsensusResult(
                primary_defect="void",
                flag_score=50,
                confidence="high",
                recommended_action="escalate",
                roles_agreed=1,
                total_roles_considered=1,
            )


# --------------------------------------------------------------------------
# run_consensus_pipeline - wiring test (fake clients, no network)
# --------------------------------------------------------------------------

class TestRunConsensusPipeline:
    def test_wires_all_three_roles_and_resolves_when_history_available(self) -> None:
        context = _sample_context()
        grid = _sample_grid()
        previous_visits = [
            HistoricalVisit(visit_sequence=1, corrected_velocity_kmps=4.2),
            HistoricalVisit(visit_sequence=2, corrected_velocity_kmps=4.0),
        ]

        role_1_client = FakeClaudeClient(_role_json("void", 90, "escalate"))
        role_2_client = FakeClaudeClient(_role_json("void", 85, "escalate"))
        role_3_client = FakeClaudeClient(_role_json("void", 88, "escalate"))

        result = run_consensus_pipeline(
            context,
            grid,
            previous_visits,
            role_1_client=role_1_client,
            role_2_client=role_2_client,
            role_3_client=role_3_client,
        )

        assert isinstance(result, ConsensusResult)
        assert result.primary_defect == "void"
        assert result.confidence == ConsensusConfidence.HIGH
        assert result.total_roles_considered == 3
        assert role_1_client.call_count == 1
        assert role_2_client.call_count == 1
        assert role_3_client.call_count == 1

    def test_falls_back_to_two_roles_when_history_insufficient(self) -> None:
        context = _sample_context()
        grid = _sample_grid()
        previous_visits: list = []  # fewer than 2 -> Role 3 stays inactive

        role_1_client = FakeClaudeClient(_role_json("crack", 70, "retest"))
        role_2_client = FakeClaudeClient(_role_json("crack", 65, "monitor"))
        role_3_client = FakeClaudeClient(_role_json("crack", 60, "monitor"))

        result = run_consensus_pipeline(
            context,
            grid,
            previous_visits,
            role_1_client=role_1_client,
            role_2_client=role_2_client,
            role_3_client=role_3_client,
        )

        assert result.total_roles_considered == 2
        assert result.confidence == ConsensusConfidence.MEDIUM
        assert role_3_client.call_count == 0  # Role 3 never called the API
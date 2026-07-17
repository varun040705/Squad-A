"""
tests/test_e2_executive_summary_report_assembly.py

Unit tests for Segment E-2: executive summary, observation table, and
report assembly. Includes the required integration test that runs the
full E-1 -> E-2 pipeline on a synthetic element.

No live Anthropic API calls are made anywhere in this file.
"""

from __future__ import annotations

import pytest

from modules.upv.c1_role_prompts import RecommendedAction
from modules.upv.e1_element_assessment_paragraph import (
    ElementAssessmentInput,
    run_generate_element_paragraph,
)
from modules.upv.e2_report_assembly import (
    AssembledReport,
    ExecutiveSummaryResult,
    ObservationRow,
    ProjectSummaryInput,
    SummaryValidationError,
    assemble_report,
    build_executive_summary_prompt,
    build_observation_table,
    run_generate_executive_summary,
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


GOOD_SUMMARY = (
    "A total of 24 elements were tested across the project, with 18 "
    "elements passing, 5 flagged for further review, and 1 failing "
    "outright. The most critical finding was a localised void identified "
    "in column C-07, requiring core extraction prior to further loading. "
    "Overall, targeted retesting of the flagged elements is recommended "
    "before the project proceeds to the next construction stage."
)

GOOD_ELEMENT_PARAGRAPH = (
    "Ultrasonic Pulse Velocity testing of column C-07 was carried out in "
    "accordance with IS 13311 Part 1 using the direct transmission method "
    "at a concrete age of 28 days. A mean pulse velocity of 3.42 km/s was "
    "recorded across 9 test locations, classifying the concrete as medium "
    "quality. Test point P5 recorded an anomalously low velocity, "
    "indicating a probable localised void. Core extraction at P5 is "
    "recommended prior to application of structural loading."
)


def _sample_summary_input(**overrides) -> ProjectSummaryInput:
    defaults = dict(
        project_id="PRJ-1",
        total_elements=24,
        passed_count=18,
        flagged_count=5,
        failed_count=1,
        most_critical_finding="localised void in column C-07",
        element_velocities_kmps=[3.42, 4.1, 3.95, 2.8],
    )
    defaults.update(overrides)
    return ProjectSummaryInput(**defaults)


def _sample_observation_row(**overrides) -> dict:
    defaults = dict(
        element_ref="C-07",
        test_point_count=9,
        mean_velocity_kmps=3.42,
        grade="Medium",
        defect="Void at P5",
        action="Core extraction",
    )
    defaults.update(overrides)
    return defaults


def _sample_element_input(**overrides) -> ElementAssessmentInput:
    defaults = dict(
        element_ref="C-07",
        element_type="column",
        transmission_mode="direct",
        concrete_age_days=28,
        mean_velocity_kmps=3.42,
        classification="medium",
        test_point_ids=[f"P{i}" for i in range(1, 10)],
        primary_defect="void",
        defect_point_ids=["P5"],
        defect_z_score=3.4,
        recommended_action=RecommendedAction.RETEST,
    )
    defaults.update(overrides)
    return ElementAssessmentInput(**defaults)


# --------------------------------------------------------------------------
# ObservationRow / build_observation_table - deterministic, no AI
# --------------------------------------------------------------------------

class TestObservationRow:
    def test_valid_row_constructs(self) -> None:
        row = ObservationRow(**_sample_observation_row())
        assert row.element_ref == "C-07"

    def test_rejects_non_positive_velocity(self) -> None:
        with pytest.raises(Exception):
            ObservationRow(**_sample_observation_row(mean_velocity_kmps=0))

    def test_rejects_zero_test_point_count(self) -> None:
        with pytest.raises(Exception):
            ObservationRow(**_sample_observation_row(test_point_count=0))

    def test_rejects_blank_defect(self) -> None:
        with pytest.raises(Exception):
            ObservationRow(**_sample_observation_row(defect="   "))


class TestBuildObservationTable:
    def test_builds_rows_directly_from_database_dicts(self) -> None:
        rows_data = [
            _sample_observation_row(),
            _sample_observation_row(element_ref="C-08", defect="None", action="None required"),
        ]

        table = build_observation_table(rows_data)

        assert len(table) == 2
        assert table[0].element_ref == "C-07"
        assert table[1].element_ref == "C-08"

    def test_table_matches_database_rows_exactly(self) -> None:
        row_data = _sample_observation_row()
        table = build_observation_table([row_data])

        assert table[0].test_point_count == row_data["test_point_count"]
        assert table[0].mean_velocity_kmps == row_data["mean_velocity_kmps"]
        assert table[0].grade == row_data["grade"]

    def test_empty_input_produces_empty_table(self) -> None:
        assert build_observation_table([]) == []

    def test_invalid_row_raises_rather_than_dropping(self) -> None:
        rows_data = [_sample_observation_row(mean_velocity_kmps=-1)]
        with pytest.raises(Exception):
            build_observation_table(rows_data)


# --------------------------------------------------------------------------
# ProjectSummaryInput schema
# --------------------------------------------------------------------------

class TestProjectSummaryInputModel:
    def test_valid_input_constructs(self) -> None:
        input_data = _sample_summary_input()
        assert input_data.project_id == "PRJ-1"

    def test_rejects_counts_that_do_not_sum_to_total(self) -> None:
        with pytest.raises(Exception):
            _sample_summary_input(total_elements=24, passed_count=10, flagged_count=5, failed_count=1)

    def test_rejects_blank_most_critical_finding(self) -> None:
        with pytest.raises(Exception):
            _sample_summary_input(most_critical_finding="   ")

    def test_rejects_empty_velocity_list(self) -> None:
        with pytest.raises(Exception):
            _sample_summary_input(element_velocities_kmps=[])


# --------------------------------------------------------------------------
# Executive summary - AI generated
# --------------------------------------------------------------------------

class TestBuildExecutiveSummaryPrompt:
    def test_prompt_includes_counts_and_finding(self) -> None:
        input_data = _sample_summary_input()
        prompt = build_executive_summary_prompt(input_data)

        assert "24" in prompt
        assert "localised void in column C-07" in prompt

    def test_prompt_instructs_no_per_element_velocity(self) -> None:
        input_data = _sample_summary_input()
        prompt = build_executive_summary_prompt(input_data)
        assert "velocity" in prompt.lower()


class TestRunGenerateExecutiveSummary:
    def test_returns_valid_summary_result(self) -> None:
        input_data = _sample_summary_input()
        client = FakeClaudeClient(GOOD_SUMMARY)

        result = run_generate_executive_summary(input_data, client=client)

        assert isinstance(result, ExecutiveSummaryResult)
        assert result.project_id == "PRJ-1"
        assert result.summary == GOOD_SUMMARY
        assert client.call_count == 1

    def test_system_prompt_forbids_per_element_velocity_and_hedging(self) -> None:
        input_data = _sample_summary_input()
        client = FakeClaudeClient(GOOD_SUMMARY)

        run_generate_executive_summary(input_data, client=client)

        system_prompt_lower = client.last_system_prompt.lower()
        assert "km/s" in system_prompt_lower
        assert "hedging" in system_prompt_lower

    def test_raises_when_summary_leaks_a_known_element_velocity(self) -> None:
        input_data = _sample_summary_input()
        bad_summary = GOOD_SUMMARY + " Element C-07 recorded 3.42 km/s."
        client = FakeClaudeClient(bad_summary)

        with pytest.raises(SummaryValidationError):
            run_generate_executive_summary(input_data, client=client)

    def test_raises_when_mpa_mentioned(self) -> None:
        input_data = _sample_summary_input()
        bad_summary = GOOD_SUMMARY.replace(
            "requiring core extraction prior to further loading",
            "equivalent to roughly 30 MPa compressive strength",
        )
        client = FakeClaudeClient(bad_summary)

        with pytest.raises(SummaryValidationError):
            run_generate_executive_summary(input_data, client=client)

    def test_raises_when_hedging_word_used(self) -> None:
        input_data = _sample_summary_input()
        bad_summary = GOOD_SUMMARY.replace(
            "requiring core extraction",
            "possibly requiring core extraction",
        )
        client = FakeClaudeClient(bad_summary)

        with pytest.raises(SummaryValidationError):
            run_generate_executive_summary(input_data, client=client)

    def test_raises_when_safe_or_unsafe_mentioned(self) -> None:
        input_data = _sample_summary_input()
        bad_summary = GOOD_SUMMARY + " The project is safe to proceed."
        client = FakeClaudeClient(bad_summary)

        with pytest.raises(SummaryValidationError):
            run_generate_executive_summary(input_data, client=client)

    def test_raises_when_too_few_sentences(self) -> None:
        input_data = _sample_summary_input()
        short_summary = "24 elements were tested. One void was found in C-07."
        client = FakeClaudeClient(short_summary)

        with pytest.raises(SummaryValidationError):
            run_generate_executive_summary(input_data, client=client)


# --------------------------------------------------------------------------
# Report assembly
# --------------------------------------------------------------------------

class TestAssembleReport:
    def test_assembles_full_payload(self) -> None:
        summary_result = ExecutiveSummaryResult(project_id="PRJ-1", summary=GOOD_SUMMARY)
        table = build_observation_table([_sample_observation_row()])

        paragraph_result = run_generate_element_paragraph(
            _sample_element_input(), client=FakeClaudeClient(GOOD_ELEMENT_PARAGRAPH)
        )

        payload = assemble_report("PRJ-1", summary_result, table, [paragraph_result])

        assert isinstance(payload, AssembledReport)
        assert payload.project_id == "PRJ-1"
        assert payload.executive_summary == GOOD_SUMMARY
        assert len(payload.observation_table) == 1
        assert len(payload.element_paragraphs) == 1
        assert payload.element_paragraphs[0].element_ref == "C-07"

    def test_assembles_with_empty_table_and_paragraphs(self) -> None:
        summary_result = ExecutiveSummaryResult(project_id="PRJ-2", summary=GOOD_SUMMARY)
        payload = assemble_report("PRJ-2", summary_result, [], [])

        assert payload.observation_table == []
        assert payload.element_paragraphs == []


# --------------------------------------------------------------------------
# Integration test: full E-1 -> E-2 pipeline on a synthetic element
# --------------------------------------------------------------------------

class TestFullE1ToE2Pipeline:
    def test_full_pipeline_runs_and_validates_all_output_rules(self) -> None:
        # --- E-1: generate the element paragraph ---
        paragraph_result = run_generate_element_paragraph(
            _sample_element_input(), client=FakeClaudeClient(GOOD_ELEMENT_PARAGRAPH)
        )

        # --- E-2: generate the executive summary ---
        summary_input = _sample_summary_input()
        summary_result = run_generate_executive_summary(
            summary_input, client=FakeClaudeClient(GOOD_SUMMARY)
        )

        # --- E-2: build the observation table (no AI) ---
        table = build_observation_table([_sample_observation_row()])

        # --- E-2: assemble the final report payload ---
        payload = assemble_report("PRJ-1", summary_result, table, [paragraph_result])

        # Full-payload assembly succeeds without errors.
        assert isinstance(payload, AssembledReport)

        # Executive summary does not leak any known per-element velocity.
        for velocity in summary_input.element_velocities_kmps:
            assert f"{velocity} km/s" not in payload.executive_summary

        # Observation table rows match the database input exactly.
        assert payload.observation_table[0].mean_velocity_kmps == 3.42
        assert payload.observation_table[0].element_ref == "C-07"

        # Element paragraph references the real point ID and IS code.
        assert "P5" in payload.element_paragraphs[0].paragraph
        assert "IS 13311 Part 1" in payload.element_paragraphs[0].paragraph

        # No forbidden language anywhere in the assembled payload.
        full_text = (
            payload.executive_summary
            + " "
            + " ".join(p.paragraph for p in payload.element_paragraphs)
        ).lower()
        for term in ("mpa", "possibly", "might", "approximately"):
            assert term not in full_text
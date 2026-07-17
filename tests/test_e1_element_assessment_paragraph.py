"""
tests/test_e1_element_assessment_paragraph.py

Unit tests for Segment E-1: element assessment paragraph generator.

No live Anthropic API calls are made. Every test injects a FakeClaudeClient
that returns canned paragraph text, matching the ClaudeMessageClient
Protocol production code depends on.
"""

from __future__ import annotations

import pytest

from modules.upv.c1_role_prompts import RecommendedAction
from modules.upv.e1_element_assessment_paragraph import (
    ElementAssessmentInput,
    ElementParagraphResult,
    ParagraphValidationError,
    build_element_paragraph_prompt,
    run_generate_element_paragraph,
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


GOOD_PARAGRAPH = (
    "Ultrasonic Pulse Velocity testing of column C-07 was carried out in "
    "accordance with IS 13311 Part 1 using the direct transmission method "
    "at a concrete age of 28 days. A mean pulse velocity of 3.42 km/s was "
    "recorded across 9 test locations, classifying the concrete as medium "
    "quality. Test point P5 recorded an anomalously low velocity, "
    "indicating a probable localised void. Core extraction at P5 is "
    "recommended prior to application of structural loading."
)


def _sample_input(**overrides) -> ElementAssessmentInput:
    defaults = dict(
        element_ref="C-07",
        element_type="column",
        transmission_mode="direct",
        concrete_age_days=28,
        mean_velocity_kmps=3.42,
        classification="medium",
        test_point_ids=["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9"],
        primary_defect="void",
        defect_point_ids=["P5"],
        defect_z_score=3.4,
        recommended_action=RecommendedAction.RETEST,
    )
    defaults.update(overrides)
    return ElementAssessmentInput(**defaults)


class TestElementAssessmentInputModel:
    def test_valid_input_constructs(self) -> None:
        input_data = _sample_input()
        assert input_data.element_ref == "C-07"

    def test_rejects_non_positive_velocity(self) -> None:
        with pytest.raises(Exception):
            _sample_input(mean_velocity_kmps=0)

    def test_rejects_blank_element_ref(self) -> None:
        with pytest.raises(Exception):
            _sample_input(element_ref="   ")

    def test_rejects_empty_test_point_ids(self) -> None:
        with pytest.raises(Exception):
            _sample_input(test_point_ids=[])

    def test_defaults_defect_fields_when_no_defect(self) -> None:
        input_data = _sample_input(primary_defect=None, defect_point_ids=[], defect_z_score=None)
        assert input_data.primary_defect is None
        assert input_data.defect_point_ids == []


class TestBuildElementParagraphPrompt:
    def test_prompt_includes_point_ids_and_classification(self) -> None:
        input_data = _sample_input()
        prompt = build_element_paragraph_prompt(input_data)

        assert "P5" in prompt
        assert "medium" in prompt
        assert "28 days" in prompt

    def test_prompt_states_no_defect_when_none_present(self) -> None:
        input_data = _sample_input(primary_defect=None, defect_point_ids=[], defect_z_score=None)
        prompt = build_element_paragraph_prompt(input_data)
        assert "Defect found: none" in prompt


class TestRunGenerateElementParagraph:
    def test_returns_valid_paragraph_result(self) -> None:
        input_data = _sample_input()
        client = FakeClaudeClient(GOOD_PARAGRAPH)

        result = run_generate_element_paragraph(input_data, client=client)

        assert isinstance(result, ElementParagraphResult)
        assert result.element_ref == "C-07"
        assert result.paragraph == GOOD_PARAGRAPH
        assert client.call_count == 1

    def test_system_prompt_forbids_mpa_and_hedging(self) -> None:
        input_data = _sample_input()
        client = FakeClaudeClient(GOOD_PARAGRAPH)

        run_generate_element_paragraph(input_data, client=client)

        system_prompt_lower = client.last_system_prompt.lower()
        assert "mpa" in system_prompt_lower
        assert "hedging" in system_prompt_lower
        assert "is 13311 part 1" in system_prompt_lower

    def test_raises_when_mpa_mentioned(self) -> None:
        input_data = _sample_input()
        bad_paragraph = GOOD_PARAGRAPH.replace(
            "classifying the concrete as medium quality",
            "equivalent to roughly 30 MPa compressive strength",
        )
        client = FakeClaudeClient(bad_paragraph)

        with pytest.raises(ParagraphValidationError):
            run_generate_element_paragraph(input_data, client=client)

    def test_raises_when_hedging_word_used(self) -> None:
        input_data = _sample_input()
        bad_paragraph = GOOD_PARAGRAPH.replace(
            "indicating a probable localised void",
            "possibly indicating a localised void",
        )
        client = FakeClaudeClient(bad_paragraph)

        with pytest.raises(ParagraphValidationError):
            run_generate_element_paragraph(input_data, client=client)

    def test_raises_when_safe_or_unsafe_mentioned(self) -> None:
        input_data = _sample_input()
        bad_paragraph = GOOD_PARAGRAPH + " The element remains safe for continued use."
        client = FakeClaudeClient(bad_paragraph)

        with pytest.raises(ParagraphValidationError):
            run_generate_element_paragraph(input_data, client=client)

    def test_raises_when_is_code_reference_missing(self) -> None:
        input_data = _sample_input()
        bad_paragraph = GOOD_PARAGRAPH.replace("IS 13311 Part 1", "the applicable code")
        client = FakeClaudeClient(bad_paragraph)

        with pytest.raises(ParagraphValidationError):
            run_generate_element_paragraph(input_data, client=client)

    def test_raises_when_no_real_point_id_referenced(self) -> None:
        input_data = _sample_input()
        bad_paragraph = GOOD_PARAGRAPH.replace("P5", "one test location")
        client = FakeClaudeClient(bad_paragraph)

        with pytest.raises(ParagraphValidationError):
            run_generate_element_paragraph(input_data, client=client)

    def test_raises_when_too_few_sentences(self) -> None:
        input_data = _sample_input()
        short_paragraph = (
            "UPV testing of column C-07 was carried out in accordance with "
            "IS 13311 Part 1. P5 showed an anomalous reading."
        )
        client = FakeClaudeClient(short_paragraph)

        with pytest.raises(ParagraphValidationError):
            run_generate_element_paragraph(input_data, client=client)

    def test_raises_when_too_many_sentences(self) -> None:
        input_data = _sample_input()
        long_paragraph = GOOD_PARAGRAPH + (
            " Additional monitoring is advised. Follow-up testing should "
            "occur within thirty days. The contractor has been notified."
        )
        client = FakeClaudeClient(long_paragraph)

        with pytest.raises(ParagraphValidationError):
            run_generate_element_paragraph(input_data, client=client)

    def test_no_defect_paragraph_passes_validation(self) -> None:
        input_data = _sample_input(primary_defect=None, defect_point_ids=[], defect_z_score=None)
        clean_paragraph = (
            "Ultrasonic Pulse Velocity testing of column C-07 was carried "
            "out in accordance with IS 13311 Part 1 using the direct "
            "transmission method at a concrete age of 28 days. A mean "
            "pulse velocity of 3.42 km/s was recorded across test points "
            "P1 through P9, classifying the concrete as medium quality. "
            "No defect was identified across any test location. Continued "
            "routine monitoring is recommended."
        )
        client = FakeClaudeClient(clean_paragraph)

        result = run_generate_element_paragraph(input_data, client=client)
        assert result.paragraph == clean_paragraph
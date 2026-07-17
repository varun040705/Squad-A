"""
OX1 NDT Platform - UPV Module
Squad E - Segment E-1: Element Assessment Paragraph Generator

Generates one 3-5 sentence prose paragraph per element via a Claude API
call, matching the format of reports submitted to government authorities.

Hard rules (AI_ENGINEERS_WORKPLAN.md, Segment E-1)
----------------------------------------------------
- State test conditions, velocity results, IS classification, defect
  found, and recommended action.
- Reference IS 13311 Part 1 by full name and number.
- Reference actual test point IDs (e.g. P5), never "one point".
- Use definitive language - no hedging ("possibly", "might", "could be",
  "approximately").
- Passive voice for findings, active voice for recommendations.
- Never mention MPa.
- The paragraph must differ every time - it is not a template
  substitution. (Not mechanically testable in a unit test; enforced by
  prompt design and left to integration/manual QA.)

Claude API Wiring
------------------
Reuses the `ClaudeMessageClient` Protocol and `RecommendedAction` enum
from Segment C-1 rather than duplicating them. Same pattern: an
injectable client for testability, a lazily-constructed real Anthropic
client in production.

Sensor Fusion Only
------------------
No Acoustic Emission. No Visual Inspection. No Electrical Surface
Resistivity.
"""

from __future__ import annotations

import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from modules.upv.c1_role_prompts import (
    AnthropicMessageClient,
    ClaudeMessageClient,
    RecommendedAction,
)


# =====================================================================
# CONSTANTS
# =====================================================================

IS_CODE_REFERENCE = "IS 13311 Part 1"

FORBIDDEN_TERMS = ("mpa", "possibly", "might", "could", "approximately", "safe", "unsafe")

MIN_PARAGRAPH_SENTENCES = 3
MAX_PARAGRAPH_SENTENCES = 5


# =====================================================================
# SCHEMAS
# =====================================================================

class ElementAssessmentInput(BaseModel):
    """Everything the paragraph generator needs about one element's visit."""

    element_ref: str = Field(..., min_length=1)
    element_type: str = Field(..., min_length=1, description="e.g. 'column', 'beam', 'slab'.")
    transmission_mode: str = Field(..., min_length=1, description="e.g. 'direct', 'semi-direct'.")
    concrete_age_days: int = Field(..., gt=0)
    mean_velocity_kmps: float = Field(..., gt=0)
    classification: str = Field(..., min_length=1, description="e.g. 'medium', 'good'.")
    test_point_ids: List[str] = Field(..., min_length=1)
    primary_defect: Optional[str] = Field(default=None)
    defect_point_ids: List[str] = Field(default_factory=list)
    defect_z_score: Optional[float] = Field(default=None)
    recommended_action: RecommendedAction = Field(...)

    @field_validator("element_ref", "element_type", "transmission_mode", "classification")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Value cannot be blank.")
        return v


class ElementParagraphResult(BaseModel):
    """Validated paragraph output for one element."""

    element_ref: str = Field(...)
    paragraph: str = Field(..., min_length=1)


class ParagraphValidationError(ValueError):
    """Raised when a generated paragraph violates a hard output rule."""


# =====================================================================
# SYSTEM PROMPT
# =====================================================================

SYSTEM_PROMPT_ELEMENT_PARAGRAPH = f"""You are a structural engineering report
writer producing one paragraph of an Ultrasonic Pulse Velocity (UPV) test
report submitted to a government authority.

Write ONE paragraph of 3 to 5 sentences for the given element. The
paragraph must:
- State the test conditions (transmission mode, concrete age), the
  velocity result, the IS classification, any defect found, and the
  recommended action.
- Reference "{IS_CODE_REFERENCE}" by its full name and number, exactly
  as written here.
- Reference the actual test point IDs given to you (e.g. "P5") -
  never say "one point" or "a test location" instead of the real ID.
- Use definitive language. NEVER use hedging words such as "possibly",
  "might", "could be", or "approximately".
- Use passive voice for findings ("A mean pulse velocity of X was
  recorded...") and active voice for recommendations ("Core extraction
  at P5 is recommended...").
- NEVER mention compressive strength or MPa.
- NEVER say "safe" or "unsafe" - that is a licensed engineer's call.
- The paragraph must be original prose for this specific element's data
  - do not reuse boilerplate sentence structure from other reports.

Respond with ONLY the paragraph text. No preamble, no heading, no
Markdown, no JSON - just the paragraph itself.
"""


# =====================================================================
# CLIENT RESOLUTION
# =====================================================================

def _resolve_client(client: Optional[ClaudeMessageClient]) -> ClaudeMessageClient:
    """Return the supplied client, or lazily build the real Anthropic one."""
    if client is not None:
        return client
    return AnthropicMessageClient()


# =====================================================================
# PROMPT BUILDER
# =====================================================================

def build_element_paragraph_prompt(input_data: ElementAssessmentInput) -> str:
    """Build the user-turn prompt for the element paragraph generator."""
    defect_line = (
        f"Defect found: {input_data.primary_defect} at point(s) "
        f"{', '.join(input_data.defect_point_ids)}"
        + (
            f" (Z-score: {input_data.defect_z_score:.1f})"
            if input_data.defect_z_score is not None
            else ""
        )
        if input_data.primary_defect
        else "Defect found: none - all test points within expected range."
    )

    return (
        f"Element reference: {input_data.element_ref} ({input_data.element_type})\n"
        f"Transmission mode: {input_data.transmission_mode}\n"
        f"Concrete age at test: {input_data.concrete_age_days} days\n"
        f"Mean pulse velocity: {input_data.mean_velocity_kmps:.2f} km/s\n"
        f"IS classification: {input_data.classification}\n"
        f"Test point IDs: {', '.join(input_data.test_point_ids)}\n"
        f"{defect_line}\n"
        f"Recommended action: {input_data.recommended_action.value}\n\n"
        "Write the paragraph now, following every rule in your system prompt."
    )


# =====================================================================
# VALIDATION
# =====================================================================

def _count_sentences(paragraph: str) -> int:
    sentences = [s for s in re.split(r"[.!?]+", paragraph) if s.strip()]
    return len(sentences)


def _validate_paragraph(paragraph: str, input_data: ElementAssessmentInput) -> None:
    """Enforce the hard output rules against a generated paragraph."""
    lowered = paragraph.lower()

    for term in FORBIDDEN_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", lowered):
            raise ParagraphValidationError(
                f"Paragraph contains forbidden term '{term}': {paragraph!r}"
            )

    if IS_CODE_REFERENCE.lower() not in lowered:
        raise ParagraphValidationError(
            f"Paragraph does not reference '{IS_CODE_REFERENCE}': {paragraph!r}"
        )

    if not any(point_id in paragraph for point_id in input_data.test_point_ids):
        raise ParagraphValidationError(
            f"Paragraph does not reference any real test point ID: {paragraph!r}"
        )

    sentence_count = _count_sentences(paragraph)
    if not (MIN_PARAGRAPH_SENTENCES <= sentence_count <= MAX_PARAGRAPH_SENTENCES):
        raise ParagraphValidationError(
            f"Paragraph has {sentence_count} sentences; expected "
            f"{MIN_PARAGRAPH_SENTENCES}-{MAX_PARAGRAPH_SENTENCES}: {paragraph!r}"
        )


# =====================================================================
# PUBLIC ENTRY POINT
# =====================================================================

def run_generate_element_paragraph(
    input_data: ElementAssessmentInput,
    client: Optional[ClaudeMessageClient] = None,
) -> ElementParagraphResult:
    """
    Generate and validate the assessment paragraph for one element.

    Raises ParagraphValidationError if the generated text violates any
    hard output rule (MPa mention, hedging language, missing IS 13311
    Part 1 reference, missing real test point ID, or wrong sentence
    count).
    """
    active_client = _resolve_client(client)
    user_prompt = build_element_paragraph_prompt(input_data)

    raw_text = active_client.create_message(
        system_prompt=SYSTEM_PROMPT_ELEMENT_PARAGRAPH,
        user_prompt=user_prompt,
    )
    paragraph = raw_text.strip()

    _validate_paragraph(paragraph, input_data)

    return ElementParagraphResult(element_ref=input_data.element_ref, paragraph=paragraph)


# =====================================================================
# PUBLIC EXPORTS
# =====================================================================

__all__ = [
    "ElementAssessmentInput",
    "ElementParagraphResult",
    "ParagraphValidationError",
    "SYSTEM_PROMPT_ELEMENT_PARAGRAPH",
    "build_element_paragraph_prompt",
    "run_generate_element_paragraph",
]
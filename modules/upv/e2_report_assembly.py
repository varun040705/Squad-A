"""
OX1 NDT Platform - UPV Module
Squad E - Segment E-2: Executive Summary, Observation Table & Report Assembly

Three distinct pieces:

1. Executive summary (ONE per project, AI-generated via Claude): a single
   paragraph covering how many elements were tested, how many
   passed/flagged/failed, the most critical finding, and the overall
   recommendation. Must NEVER contain any per-element velocity number -
   it summarises only.

2. Observation table (auto-generated from the database, NOT AI-written):
   plain structured data - element ref, test points, mean velocity,
   grade, defect, action - wired directly from the database query.
   No Claude call happens anywhere in this path.

3. Report assembly: combines the executive summary, the observation
   table, and Segment E-1's per-element paragraphs into a single
   structured JSON payload for the frontend's PDF generator.

Claude API Wiring
------------------
Reuses the `ClaudeMessageClient` Protocol and `AnthropicMessageClient`
from Segment C-1 - same injectable-client pattern used throughout the
repo, no duplicate client abstraction.

Sensor Fusion Only
------------------
No Acoustic Emission. No Visual Inspection. No Electrical Surface
Resistivity.
"""

from __future__ import annotations

import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from modules.upv.c1_role_prompts import AnthropicMessageClient, ClaudeMessageClient
from modules.upv.e1_element_assessment_paragraph import (
    FORBIDDEN_TERMS,
    IS_CODE_REFERENCE,
    ElementParagraphResult,
)


# =====================================================================
# CONSTANTS
# =====================================================================

MIN_SUMMARY_SENTENCES = 3
MAX_SUMMARY_SENTENCES = 6

# Matches things like "3.42 km/s" or "3.42km/s" so we can verify the
# executive summary never leaks a per-element velocity figure.
VELOCITY_MENTION_PATTERN = re.compile(r"(\d+\.\d+)\s*km/s", re.IGNORECASE)


# =====================================================================
# SCHEMAS - OBSERVATION TABLE (database-sourced, no AI)
# =====================================================================

class ObservationRow(BaseModel):
    """
    One row of the observation table. This is a straight database
    projection - every field here is expected to already exist in the
    database query result. No AI involvement and no derived judgement
    calls happen in this schema or its builder function.
    """

    element_ref: str = Field(..., min_length=1)
    test_point_count: int = Field(..., ge=1)
    mean_velocity_kmps: float = Field(..., gt=0)
    grade: str = Field(..., min_length=1)
    defect: str = Field(..., min_length=1, description="e.g. 'Void at P5' or 'None'.")
    action: str = Field(..., min_length=1, description="e.g. 'Core extraction'.")

    @field_validator("element_ref", "grade", "defect", "action")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Value cannot be blank.")
        return v


def build_observation_table(rows_data: List[dict]) -> List[ObservationRow]:
    """
    Build the observation table directly from database query rows.

    Pure, deterministic, no AI call - each dict is simply validated
    into an ObservationRow. If a row fails validation, this raises
    rather than silently dropping a database record.
    """
    return [ObservationRow(**row) for row in rows_data]


# =====================================================================
# SCHEMAS - EXECUTIVE SUMMARY (AI-generated)
# =====================================================================

class ProjectSummaryInput(BaseModel):
    """Project-level counts and the most critical finding, for the executive summary prompt."""

    project_id: str = Field(..., min_length=1)
    total_elements: int = Field(..., ge=1)
    passed_count: int = Field(..., ge=0)
    flagged_count: int = Field(..., ge=0)
    failed_count: int = Field(..., ge=0)
    most_critical_finding: str = Field(..., min_length=1)
    element_velocities_kmps: List[float] = Field(
        ...,
        min_length=1,
        description=(
            "Per-element mean velocities, used only to validate that none "
            "of them leak into the generated summary text."
        ),
    )

    @field_validator("project_id", "most_critical_finding")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Value cannot be blank.")
        return v

    @model_validator(mode="after")
    def _counts_must_sum_to_total(self) -> "ProjectSummaryInput":
        if self.passed_count + self.flagged_count + self.failed_count != self.total_elements:
            raise ValueError(
                "passed_count + flagged_count + failed_count must equal total_elements."
            )
        return self


class ExecutiveSummaryResult(BaseModel):
    """Validated executive summary output for one project."""

    project_id: str = Field(...)
    summary: str = Field(..., min_length=1)


class SummaryValidationError(ValueError):
    """Raised when a generated executive summary violates a hard output rule."""


# =====================================================================
# SYSTEM PROMPT
# =====================================================================

SYSTEM_PROMPT_EXECUTIVE_SUMMARY = f"""You are a structural engineering report
writer producing the executive summary of a project-level Ultrasonic Pulse
Velocity (UPV) test report submitted to a government authority.

Write ONE paragraph of 3 to 6 sentences covering:
- How many elements were tested in total.
- How many passed, how many were flagged, and how many failed.
- The single most critical finding across the project.
- The overall recommendation for the project.

Rules:
- NEVER state any individual element's velocity reading or any specific
  numeric km/s value - this is a summary, not a per-element report.
  Per-element detail belongs in the individual element paragraphs, not
  here.
- Use definitive language. NEVER use hedging words such as "possibly",
  "might", "could be", or "approximately".
- NEVER mention compressive strength or MPa.
- NEVER say "safe" or "unsafe" - that is a licensed engineer's call.
- Reference "{IS_CODE_REFERENCE}" if relevant to the recommendation.

Respond with ONLY the summary paragraph text. No preamble, no heading,
no Markdown, no JSON - just the paragraph itself.
"""


def build_executive_summary_prompt(input_data: ProjectSummaryInput) -> str:
    """Build the user-turn prompt for the executive summary generator."""
    return (
        f"Project ID: {input_data.project_id}\n"
        f"Total elements tested: {input_data.total_elements}\n"
        f"Passed: {input_data.passed_count}\n"
        f"Flagged: {input_data.flagged_count}\n"
        f"Failed: {input_data.failed_count}\n"
        f"Most critical finding: {input_data.most_critical_finding}\n\n"
        "Write the executive summary now, following every rule in your "
        "system prompt. Do not state any individual element's velocity."
    )


# =====================================================================
# CLIENT RESOLUTION
# =====================================================================

def _resolve_client(client: Optional[ClaudeMessageClient]) -> ClaudeMessageClient:
    """Return the supplied client, or lazily build the real Anthropic one."""
    if client is not None:
        return client
    return AnthropicMessageClient()


# =====================================================================
# VALIDATION
# =====================================================================

def _count_sentences(text: str) -> int:
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    return len(sentences)


def _validate_executive_summary(summary: str, input_data: ProjectSummaryInput) -> None:
    """Enforce the hard output rules against a generated executive summary."""
    lowered = summary.lower()

    for term in FORBIDDEN_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", lowered):
            raise SummaryValidationError(
                f"Executive summary contains forbidden term '{term}': {summary!r}"
            )

    mentioned_velocities = {float(match) for match in VELOCITY_MENTION_PATTERN.findall(summary)}
    leaked = mentioned_velocities.intersection(
        {round(v, 2) for v in input_data.element_velocities_kmps}
    )
    if leaked:
        raise SummaryValidationError(
            f"Executive summary leaks per-element velocity figure(s) {leaked}: {summary!r}"
        )

    sentence_count = _count_sentences(summary)
    if not (MIN_SUMMARY_SENTENCES <= sentence_count <= MAX_SUMMARY_SENTENCES):
        raise SummaryValidationError(
            f"Executive summary has {sentence_count} sentences; expected "
            f"{MIN_SUMMARY_SENTENCES}-{MAX_SUMMARY_SENTENCES}: {summary!r}"
        )


# =====================================================================
# PUBLIC ENTRY POINT - EXECUTIVE SUMMARY
# =====================================================================

def run_generate_executive_summary(
    input_data: ProjectSummaryInput,
    client: Optional[ClaudeMessageClient] = None,
) -> ExecutiveSummaryResult:
    """
    Generate and validate the project-level executive summary.

    Raises SummaryValidationError if the generated text violates any
    hard output rule (MPa mention, hedging language, a leaked
    per-element velocity figure, or wrong sentence count).
    """
    active_client = _resolve_client(client)
    user_prompt = build_executive_summary_prompt(input_data)

    raw_text = active_client.create_message(
        system_prompt=SYSTEM_PROMPT_EXECUTIVE_SUMMARY,
        user_prompt=user_prompt,
    )
    summary = raw_text.strip()

    _validate_executive_summary(summary, input_data)

    return ExecutiveSummaryResult(project_id=input_data.project_id, summary=summary)


# =====================================================================
# SCHEMAS - REPORT ASSEMBLY
# =====================================================================

class AssembledReport(BaseModel):
    """
    Final structured payload handed to the frontend's PDF generator.
    Pure assembly - no AI call happens here, even though two of its
    three components (executive_summary, element_paragraphs) were
    themselves AI-generated upstream.
    """

    project_id: str = Field(...)
    executive_summary: str = Field(..., min_length=1)
    observation_table: List[ObservationRow] = Field(default_factory=list)
    element_paragraphs: List[ElementParagraphResult] = Field(default_factory=list)


def assemble_report(
    project_id: str,
    executive_summary_result: ExecutiveSummaryResult,
    observation_table: List[ObservationRow],
    element_paragraphs: List[ElementParagraphResult],
) -> AssembledReport:
    """
    Combine the executive summary, observation table, and per-element
    paragraphs into the final report payload.
    """
    return AssembledReport(
        project_id=project_id,
        executive_summary=executive_summary_result.summary,
        observation_table=observation_table,
        element_paragraphs=element_paragraphs,
    )


# =====================================================================
# PUBLIC EXPORTS
# =====================================================================

__all__ = [
    "ObservationRow",
    "build_observation_table",
    "ProjectSummaryInput",
    "ExecutiveSummaryResult",
    "SummaryValidationError",
    "SYSTEM_PROMPT_EXECUTIVE_SUMMARY",
    "build_executive_summary_prompt",
    "run_generate_executive_summary",
    "AssembledReport",
    "assemble_report",
]
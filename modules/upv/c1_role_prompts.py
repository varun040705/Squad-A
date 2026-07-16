"""
OX1 NDT Platform - UPV Module
Squad C - Segment C-1: Three Analytical Role Prompts

Three independent Claude API roles analyse the same velocity grid from
three different angles. Each role is a self-contained, independently
testable function that returns a role-scoped opinion. Segment C-2's
resolver (pure Python, no AI call) later reconciles the three opinions
into one consensus output.

Roles
-----
1. IS Code Checker        - strict IS 13311 compliance, uses Squad A's
                             effective_bands, no interpretation.
2. Spatial Analyst        - geometry of the velocity grid only, isolated
                             vs clustered vs linear low-velocity points,
                             ignores IS thresholds entirely.
3. Historical Comparator  - trend across previous visits to the same
                             element. Requires at least 2 prior visit
                             records to activate; returns None otherwise.

Claude API Wiring
------------------
The Anthropic API call is wrapped behind the `ClaudeMessageClient`
Protocol so every role function is independently testable with a fake
client (no live API key required in tests) while still using the real
Anthropic SDK call shape in production. If no client is supplied, a
lazily-constructed `AnthropicMessageClient` talks to the real API.

Sensor Fusion Only
------------------
No Acoustic Emission. No Visual Inspection. No Electrical Surface
Resistivity.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Dict, List, Optional, Protocol

from pydantic import BaseModel, Field, field_validator

from modules.upv.b1_point_level_detectors import GridPoint, VelocityGrid
from modules.upv.squad_a_context_engine import FinalContextObject


# =====================================================================
# CONSTANTS
# =====================================================================

CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_MAX_TOKENS = 1000

MIN_PRIOR_VISITS_FOR_HISTORICAL_ROLE = 2

# Global "AI must never do" rules (AI_ENGINEERS_WORKPLAN.md, SHARED RULES),
# repeated verbatim inside every role's system prompt.
FORBIDDEN_OUTPUT_RULES = (
    "Never output compressive strength in MPa. "
    "Never say 'safe' or 'unsafe' - that is a licensed engineer's call. "
    "Never use hedging words such as 'possibly', 'might', 'could be', "
    "'approximately'. Never invent test points - if data is insufficient, "
    "flag it, never estimate."
)


# =====================================================================
# ENUMS
# =====================================================================

class RecommendedAction(str, Enum):
    """
    Severity-ordered recommended action. Order matters - Segment C-2's
    resolver picks the MOST severe action across all three roles using
    this exact ordering.
    """
    PASS = "pass"
    MONITOR = "monitor"
    RETEST = "retest"
    FLAG_FOR_REVIEW = "flag_for_review"
    ESCALATE = "escalate"


# =====================================================================
# CLAUDE CLIENT PROTOCOL (injectable for testability)
# =====================================================================

class ClaudeMessageClient(Protocol):
    """
    Minimal interface each role function depends on. Production code
    gets a real `AnthropicMessageClient`; tests inject a fake client
    that returns canned JSON text with no network call and no API key.
    """

    def create_message(self, *, system_prompt: str, user_prompt: str) -> str:
        """Send a message to Claude and return the raw response text."""
        ...


class AnthropicMessageClient:
    """
    Default production client. Wraps the real Anthropic SDK. Imported
    lazily so the `anthropic` package is only required when this class
    is actually instantiated (tests never need it installed).
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        import anthropic  # local import - optional dependency for tests

        self._client = anthropic.Anthropic(api_key=api_key)

    def create_message(self, *, system_prompt: str, user_prompt: str) -> str:
        response = self._client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )


def _get_client(client: Optional[ClaudeMessageClient]) -> ClaudeMessageClient:
    """Return the supplied client, or lazily build the real one."""
    if client is not None:
        return client
    return AnthropicMessageClient()


# =====================================================================
# SHARED SCHEMAS
# =====================================================================

class RoleResult(BaseModel):
    """Standard output object every analytical role must return."""

    primary_defect: str = Field(...)
    flag_score: int = Field(..., ge=0, le=100)
    recommended_action: RecommendedAction = Field(...)
    reasoning: str = Field(...)

    @field_validator("primary_defect")
    @classmethod
    def _not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("primary_defect cannot be empty.")
        return v


class HistoricalVisit(BaseModel):
    """One prior UPV visit record for the same element."""

    visit_sequence: int = Field(..., ge=1, description="1 = earliest visit.")
    corrected_velocity_kmps: float = Field(..., gt=0)

    @field_validator("corrected_velocity_kmps")
    @classmethod
    def _must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("corrected_velocity_kmps must be positive.")
        return v


class ClaudeResponseParsingError(ValueError):
    """Raised when a role's Claude response cannot be parsed into a RoleResult."""


# =====================================================================
# RESPONSE PARSING
# =====================================================================

def _parse_role_response(raw_text: str) -> RoleResult:
    """
    Parse a role's raw Claude response text into a validated RoleResult.

    Claude is instructed to return JSON only, but defensively strips
    Markdown code fences in case the model wraps its answer.
    """
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ClaudeResponseParsingError(
            f"Role response was not valid JSON: {raw_text!r}"
        ) from exc

    try:
        return RoleResult(**payload)
    except Exception as exc:  # pydantic ValidationError or missing keys
        raise ClaudeResponseParsingError(
            f"Role response JSON did not match RoleResult schema: {payload!r}"
        ) from exc


# =====================================================================
# ROLE 1 - IS CODE CHECKER
# =====================================================================

SYSTEM_PROMPT_IS_CODE_CHECKER = f"""You are the IS Code Checker, one of three
independent analytical roles reviewing Ultrasonic Pulse Velocity (UPV) test
data for a concrete element under IS 13311 Part 1.

Your ONLY job is strict compliance checking against the effective quality
bands provided to you. You check each test point's velocity against the
bands - pass or fail per point - and summarise into a single role opinion.

Rules:
- Use ONLY the effective_bands thresholds supplied to you. Do not apply
  standard IS 13311 bands if aggregate-specific bands were supplied instead.
- Do not interpret spatial patterns and do not consider test history -
  that is not your role.
- Make no assumptions beyond the numbers given.
- {FORBIDDEN_OUTPUT_RULES}

Respond ONLY with a JSON object matching this exact shape, no preamble,
no Markdown fences:
{{"primary_defect": "<string>", "flag_score": <0-100 int>,
"recommended_action": "<pass|monitor|retest|flag_for_review|escalate>",
"reasoning": "<string citing real point IDs and real velocity numbers>"}}
"""


def build_is_code_checker_prompt(
    context: FinalContextObject,
    grid: VelocityGrid,
) -> str:
    """Build the user-turn prompt for Role 1 from Squad A context + grid."""
    point_lines = "\n".join(
        f"- {point.point_id}: {point.velocity_kmps:.3f} km/s"
        for point in grid.points
    )
    return (
        f"Element ID: {context.element_id}\n"
        f"Effective quality bands (km/s): {json.dumps(context.effective_bands)}\n"
        f"Confidence ceiling: {context.confidence_ceiling}\n"
        f"Test point velocities:\n{point_lines}\n\n"
        "Classify every point against the effective bands and return your "
        "role opinion as the single JSON object specified in your system "
        "prompt."
    )


def run_is_code_checker_role(
    context: FinalContextObject,
    grid: VelocityGrid,
    client: Optional[ClaudeMessageClient] = None,
) -> RoleResult:
    """Execute Role 1 (IS Code Checker) and return its opinion."""
    active_client = _get_client(client)
    user_prompt = build_is_code_checker_prompt(context, grid)
    raw_text = active_client.create_message(
        system_prompt=SYSTEM_PROMPT_IS_CODE_CHECKER,
        user_prompt=user_prompt,
    )
    return _parse_role_response(raw_text)


# =====================================================================
# ROLE 2 - SPATIAL ANALYST
# =====================================================================

SYSTEM_PROMPT_SPATIAL_ANALYST = f"""You are the Spatial Analyst, one of three
independent analytical roles reviewing Ultrasonic Pulse Velocity (UPV) test
data for a concrete element.

Your ONLY job is to read the geometric pattern of the velocity grid. You do
not know or care about IS 13311 quality thresholds - a velocity number only
matters to you in relation to its neighbours.

Consider:
- Are low-velocity points isolated single points, or do they cluster?
- Do low-velocity points form a straight geometric line (row or column)?
- Is the weakness spread evenly across the whole grid, or localised?

Rules:
- Do NOT reference IS 13311 bands, pass/fail classification, or numeric
  quality thresholds of any kind - that is not your role.
- Do NOT consider visit history - that is not your role.
- {FORBIDDEN_OUTPUT_RULES}

Respond ONLY with a JSON object matching this exact shape, no preamble,
no Markdown fences:
{{"primary_defect": "<string>", "flag_score": <0-100 int>,
"recommended_action": "<pass|monitor|retest|flag_for_review|escalate>",
"reasoning": "<string citing real point IDs and real velocity numbers>"}}
"""


def build_spatial_analyst_prompt(grid: VelocityGrid) -> str:
    """Build the user-turn prompt for Role 2 from the raw grid geometry."""
    point_lines = "\n".join(
        f"- {point.point_id} (row={point.row}, column={point.column}): "
        f"{point.velocity_kmps:.3f} km/s"
        for point in grid.points
    )
    return (
        f"Test point grid layout and velocities:\n{point_lines}\n\n"
        "Analyse only the spatial pattern of these readings and return "
        "your role opinion as the single JSON object specified in your "
        "system prompt."
    )


def run_spatial_analyst_role(
    grid: VelocityGrid,
    client: Optional[ClaudeMessageClient] = None,
) -> RoleResult:
    """Execute Role 2 (Spatial Analyst) and return its opinion."""
    active_client = _get_client(client)
    user_prompt = build_spatial_analyst_prompt(grid)
    raw_text = active_client.create_message(
        system_prompt=SYSTEM_PROMPT_SPATIAL_ANALYST,
        user_prompt=user_prompt,
    )
    return _parse_role_response(raw_text)


# =====================================================================
# ROLE 3 - HISTORICAL COMPARATOR
# =====================================================================

SYSTEM_PROMPT_HISTORICAL_COMPARATOR = f"""You are the Historical Comparator,
one of three independent analytical roles reviewing Ultrasonic Pulse
Velocity (UPV) test data for a concrete element.

Your ONLY job is to compare the current visit's velocity against prior
visits to the SAME element and describe the trend: getting worse, better,
or stable.

Rules:
- Do NOT reference IS 13311 bands or spatial geometry - that is not your
  role.
- {FORBIDDEN_OUTPUT_RULES}

Respond ONLY with a JSON object matching this exact shape, no preamble,
no Markdown fences:
{{"primary_defect": "<string>", "flag_score": <0-100 int>,
"recommended_action": "<pass|monitor|retest|flag_for_review|escalate>",
"reasoning": "<string citing real velocity numbers and visit sequence>"}}
"""


def build_historical_comparator_prompt(
    current_velocity_kmps: float,
    previous_visits: List[HistoricalVisit],
) -> str:
    """Build the user-turn prompt for Role 3 from the visit history."""
    history_lines = "\n".join(
        f"- Visit {visit.visit_sequence}: {visit.corrected_velocity_kmps:.3f} km/s"
        for visit in sorted(previous_visits, key=lambda v: v.visit_sequence)
    )
    return (
        f"Current visit velocity: {current_velocity_kmps:.3f} km/s\n"
        f"Prior visit history:\n{history_lines}\n\n"
        "Compare the current visit against this history and return your "
        "role opinion as the single JSON object specified in your system "
        "prompt."
    )


def run_historical_comparator_role(
    current_velocity_kmps: float,
    previous_visits: List[HistoricalVisit],
    client: Optional[ClaudeMessageClient] = None,
) -> Optional[RoleResult]:
    """
    Execute Role 3 (Historical Comparator).

    Returns None gracefully when fewer than
    MIN_PRIOR_VISITS_FOR_HISTORICAL_ROLE prior visit records exist - this
    role never speculates on thin history.
    """
    if len(previous_visits) < MIN_PRIOR_VISITS_FOR_HISTORICAL_ROLE:
        return None

    active_client = _get_client(client)
    user_prompt = build_historical_comparator_prompt(current_velocity_kmps, previous_visits)
    raw_text = active_client.create_message(
        system_prompt=SYSTEM_PROMPT_HISTORICAL_COMPARATOR,
        user_prompt=user_prompt,
    )
    return _parse_role_response(raw_text)


# =====================================================================
# PUBLIC EXPORTS
# =====================================================================

__all__ = [
    "RecommendedAction",
    "ClaudeMessageClient",
    "AnthropicMessageClient",
    "RoleResult",
    "HistoricalVisit",
    "ClaudeResponseParsingError",
    "SYSTEM_PROMPT_IS_CODE_CHECKER",
    "SYSTEM_PROMPT_SPATIAL_ANALYST",
    "SYSTEM_PROMPT_HISTORICAL_COMPARATOR",
    "build_is_code_checker_prompt",
    "build_spatial_analyst_prompt",
    "build_historical_comparator_prompt",
    "run_is_code_checker_role",
    "run_spatial_analyst_role",
    "run_historical_comparator_role",
]
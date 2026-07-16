"""
OX1 NDT Platform - UPV Module
Squad C - Segment C-2: Resolver Logic & Consensus Output

Reconciles the three independent role opinions produced by Segment C-1
into a single trustworthy consensus output.

This module is pure, deterministic Python - NO AI call happens here.
The only AI calls in Squad C live in Segment C-1's role functions;
`run_consensus_pipeline` simply wires those role functions together and
hands their outputs to the deterministic `resolve_roles` function.

Rules (AI_ENGINEERS_WORKPLAN.md, Segment C-2):
- Final action is always the most severe of the available roles' actions
  - never downgrade severity.
- All 3 roles agree -> confidence: high
- 2 of 3 roles agree -> confidence: medium (majority defect wins)
- All 3 roles disagree -> primary_defect: uncertain, confidence: low,
  recommended_action forced to flag_for_review
- flag_score is the weighted blend of the three roles' flag_scores
  (0.33 / 0.33 / 0.34), matching the work plan's reference resolver.

Role 3 (Historical Comparator) may legitimately be unavailable (fewer
than 2 prior visits - see Segment C-1). When that happens, this module
falls back to a 2-role resolution using only Roles 1 and 2, and records
how many roles were actually considered in `total_roles_considered` so
downstream consumers never confuse "2 of 2 agreed" with "2 of 3 agreed".

Sensor Fusion Only
------------------
No Acoustic Emission. No Visual Inspection. No Electrical Surface
Resistivity.
"""

from __future__ import annotations

from collections import Counter
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from modules.upv.b1_point_level_detectors import VelocityGrid
from modules.upv.squad_a_context_engine import FinalContextObject
from modules.upv.c1_role_prompts import (
    ClaudeMessageClient,
    HistoricalVisit,
    RecommendedAction,
    RoleResult,
    run_historical_comparator_role,
    run_is_code_checker_role,
    run_spatial_analyst_role,
)


# =====================================================================
# CONSTANTS
# =====================================================================

# Weighted blend used only when all 3 roles are available, taken
# verbatim from the work plan's reference resolver.
ROLE_1_FLAG_WEIGHT_WHEN_THREE_ROLES = 0.33
ROLE_2_FLAG_WEIGHT_WHEN_THREE_ROLES = 0.33
ROLE_3_FLAG_WEIGHT_WHEN_THREE_ROLES = 0.34

UNCERTAIN_DEFECT_LABEL = "uncertain"


# =====================================================================
# ENUMS
# =====================================================================

class ConsensusConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# =====================================================================
# SCHEMAS
# =====================================================================

class ConsensusResult(BaseModel):
    """Final, reconciled output returned by the Squad C consensus system."""

    primary_defect: str = Field(...)
    flag_score: int = Field(..., ge=0, le=100)
    confidence: ConsensusConfidence = Field(...)
    recommended_action: RecommendedAction = Field(...)
    roles_agreed: int = Field(..., ge=0)
    total_roles_considered: int = Field(..., ge=2, le=3)


# =====================================================================
# INTERNAL HELPERS
# =====================================================================

def _most_severe_action(actions: List[RecommendedAction]) -> RecommendedAction:
    """
    Return the most severe action among the given actions. Severity
    increases with `RecommendedAction`'s declaration order: pass <
    monitor < retest < flag_for_review < escalate.
    """
    severity_order = list(RecommendedAction)
    return max(actions, key=severity_order.index)


def _blended_flag_score(available: List[RoleResult]) -> int:
    """
    Blend flag_score across the available roles.

    When all 3 roles are present, use the work plan's exact reference
    weights (0.33 / 0.33 / 0.34). With only 2 roles available (Role 3
    inactive), fall back to an equal-weight mean.
    """
    if len(available) == 3:
        blended = (
            available[0].flag_score * ROLE_1_FLAG_WEIGHT_WHEN_THREE_ROLES
            + available[1].flag_score * ROLE_2_FLAG_WEIGHT_WHEN_THREE_ROLES
            + available[2].flag_score * ROLE_3_FLAG_WEIGHT_WHEN_THREE_ROLES
        )
    else:
        blended = sum(role.flag_score for role in available) / len(available)
    return round(blended)


# =====================================================================
# RESOLVER (pure Python - no AI call)
# =====================================================================

def resolve_roles(
    role_1_result: RoleResult,
    role_2_result: RoleResult,
    role_3_result: Optional[RoleResult] = None,
) -> ConsensusResult:
    """
    Deterministically reconcile 2 or 3 independent role opinions into a
    single ConsensusResult. Never downgrades the most severe recommended
    action across the available roles.

    Args:
        role_1_result: IS Code Checker opinion (always available).
        role_2_result: Spatial Analyst opinion (always available).
        role_3_result: Historical Comparator opinion, or None if fewer
            than 2 prior visits existed (see Segment C-1).

    Returns:
        ConsensusResult with the reconciled defect, blended flag_score,
        confidence tier, final recommended action, and role agreement
        counts.
    """
    available = [role_1_result, role_2_result]
    if role_3_result is not None:
        available.append(role_3_result)

    total_roles = len(available)

    defects = [role.primary_defect for role in available]
    actions = [role.recommended_action for role in available]

    defect_counts = Counter(defects)
    top_defect, top_count = defect_counts.most_common(1)[0]

    final_action = _most_severe_action(actions)
    final_defect = top_defect

    if total_roles == 3:
        if top_count == 3:
            confidence = ConsensusConfidence.HIGH
        elif top_count == 2:
            confidence = ConsensusConfidence.MEDIUM
        else:
            confidence = ConsensusConfidence.LOW
            final_defect = UNCERTAIN_DEFECT_LABEL
            final_action = RecommendedAction.FLAG_FOR_REVIEW
    else:  # total_roles == 2, Role 3 (Historical Comparator) was unavailable
        if top_count == 2:
            confidence = ConsensusConfidence.MEDIUM
        else:
            confidence = ConsensusConfidence.LOW
            final_defect = UNCERTAIN_DEFECT_LABEL
            final_action = RecommendedAction.FLAG_FOR_REVIEW

    flag_score = _blended_flag_score(available)

    return ConsensusResult(
        primary_defect=final_defect,
        flag_score=flag_score,
        confidence=confidence,
        recommended_action=final_action,
        roles_agreed=top_count,
        total_roles_considered=total_roles,
    )


# =====================================================================
# WIRING - runs the three C-1 roles, then resolves them
# =====================================================================

def run_consensus_pipeline(
    context: FinalContextObject,
    grid: VelocityGrid,
    previous_visits: List[HistoricalVisit],
    role_1_client: Optional[ClaudeMessageClient] = None,
    role_2_client: Optional[ClaudeMessageClient] = None,
    role_3_client: Optional[ClaudeMessageClient] = None,
) -> ConsensusResult:
    """
    Full Squad C pipeline: run all three Segment C-1 roles against the
    given context/grid/history, then reconcile them with the pure
    Python resolver.

    Each role may be given its own injectable Claude client (useful for
    testing); when omitted, each role lazily builds its own real
    Anthropic client.
    """
    role_1_result = run_is_code_checker_role(context, grid, client=role_1_client)
    role_2_result = run_spatial_analyst_role(grid, client=role_2_client)
    role_3_result = run_historical_comparator_role(
        context.corrected_velocity_kmps,
        previous_visits,
        client=role_3_client,
    )

    return resolve_roles(role_1_result, role_2_result, role_3_result)


# =====================================================================
# PUBLIC EXPORTS
# =====================================================================

__all__ = [
    "ConsensusConfidence",
    "ConsensusResult",
    "resolve_roles",
    "run_consensus_pipeline",
]
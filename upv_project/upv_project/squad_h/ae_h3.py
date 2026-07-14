"""
ae_h3.py

H-3 : Final Context Builder

Author: Sai Varun
Project: OX1 - Squad H
"""

from squad_h.models import (
    H2Result,
    AcousticEmissionContext,
)
from squad_h.grade_engine import determine_grade
from squad_h.config import CONFIDENCE_CEILING


def apply_confidence_ceiling(confidence: float) -> float:
    """
    Apply the maximum confidence ceiling.
    """

    return min(confidence, CONFIDENCE_CEILING)


def build_context(
    inspection_id: str,
    h2_result: H2Result,
) -> AcousticEmissionContext:
    """
    Build the final Acoustic Emission Context.
    """

    grade = determine_grade(h2_result)

    confidence = apply_confidence_ceiling(
        h2_result.trend.confidence
    )

    summary = (
        f"Grade {grade.value} "
        f"with {h2_result.eligible_hits} eligible hits "
        f"out of {h2_result.total_hits} total hits."
    )

    return AcousticEmissionContext(
        inspection_id=inspection_id,
        grade=grade,
        confidence=confidence,
        confidence_ceiling=CONFIDENCE_CEILING,

        localization=h2_result.localization,
        trend=h2_result.trend,
        load_history=h2_result.load_history,

        total_hits=h2_result.total_hits,
        eligible_hits=h2_result.eligible_hits,

        summary=summary,
    )

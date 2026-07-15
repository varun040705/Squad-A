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
    element_ref: str,
    h2_result: H2Result,
) -> AcousticEmissionContext:
    """
    Build the final Acoustic Emission Context, published downstream to
    Sensor Fusion. Matches the flattened schema in the workplan.

    If grading can't be determined (no load-history data yet), we do NOT
    invent a grade -- not even a "conservative" one. `grade` stays None
    and "grade_undetermined" is added to flags, so Sensor Fusion can treat
    this element as pending rather than receiving a fabricated severity.
    This mirrors the workplan's own rule: insufficient data gets flagged,
    never estimated -- that principle applies to grading exactly the same
    way it applies to location and AE event data.
    """

    flags = list(h2_result.flags)
    grade = None

    try:
        grade = determine_grade(h2_result)
    except ValueError as e:
        flags.append("grade_undetermined")
        flags.append(str(e))

    confidence = apply_confidence_ceiling(h2_result.trend.confidence)

    hits_localized = (
        h2_result.eligible_hits if h2_result.localization.success else 0
    )

    if grade is not None:
        summary = (
            f"Grade {grade.value} "
            f"with {h2_result.eligible_hits} eligible hits "
            f"out of {h2_result.total_hits} total hits."
        )
    else:
        summary = (
            f"Grade undetermined -- load-history data not yet available. "
            f"{h2_result.eligible_hits} eligible hits out of {h2_result.total_hits} total hits."
        )

    return AcousticEmissionContext(
        method="AE",
        element_ref=element_ref,
        inspection_id=inspection_id,

        hits_total=h2_result.total_hits,
        hits_localized=hits_localized,

        b_value_trend=h2_result.trend.trend,
        felicity_ratio=h2_result.load_history.felicity_ratio,
        calm_ratio=h2_result.load_history.calm_ratio,

        grade=grade,
        confidence=confidence,
        confidence_ceiling=CONFIDENCE_CEILING,

        flags=flags,
        summary=summary,
    )
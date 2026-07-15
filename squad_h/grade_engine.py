from squad_h.models import H2Result, AEGrade
from squad_h.config import (
    FELICITY_GRADE_II_MIN,
    FELICITY_GRADE_III_MIN,
    CALM_RATIO_HIGH_THRESHOLD,
)


def determine_grade(h2_result: H2Result) -> AEGrade:
    """
    Per workplan H-3 grading table -- driven by Felicity ratio (Kaiser
    effect breakdown) and calm ratio, NOT by localization success or
    b-value trend. Those are independent signals surfaced as flags on
    the context object, not grading inputs: a hit that fails to localize
    still tells you something about damage severity via its Felicity
    ratio, and shouldn't be auto-downgraded to Grade IV just because
    fewer than 4 sensors caught it.

    If neither ratio is available yet (no load-history data supplied),
    we cannot responsibly assign any grade -- raising rather than
    guessing, since silently returning a default grade would violate
    the "never estimate" principle that runs through this whole squad.
    """

    felicity_ratio = h2_result.load_history.felicity_ratio
    calm_ratio = h2_result.load_history.calm_ratio

    if felicity_ratio is None and calm_ratio is None:
        raise ValueError(
            "cannot_determine_grade: no load-history data available "
            "(felicity_ratio and calm_ratio are both None)"
        )

    if calm_ratio is not None and calm_ratio > CALM_RATIO_HIGH_THRESHOLD:
        return AEGrade.IV

    if felicity_ratio is None:
        raise ValueError(
            "cannot_determine_grade: calm_ratio available but felicity_ratio "
            "is None, and grading bands are defined by felicity_ratio"
        )

    if felicity_ratio < FELICITY_GRADE_III_MIN:
        return AEGrade.IV
    if felicity_ratio < FELICITY_GRADE_II_MIN:
        return AEGrade.III
    if felicity_ratio < 1.0:
        return AEGrade.II
    return AEGrade.I
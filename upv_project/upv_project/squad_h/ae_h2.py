"""
ae_h2.py

H-2 : Localization and Trend Analysis

Author: Sai Varun
Project: OX1 - Squad H
"""

from squad_h.models import (
    H1Result,
    H2Result,
    LocalizationResult,
    TrendResult,
    LoadHistoryResult,
)

from squad_h.config import (
    MIN_LOCALIZATION_SENSORS,
)


def validate_sensor_count(h1_result: H1Result) -> int:
    """
    Count unique sensors from eligible hits.
    """

    sensors = {
        hit.sensor_id
        for hit in h1_result.eligible_hits
    }

    return len(sensors)


def localize_hits(h1_result: H1Result) -> LocalizationResult:
    """
    Perform localization.

    Current version:
    Only validates sensor count.
    """

    sensor_count = validate_sensor_count(h1_result)

    if sensor_count < MIN_LOCALIZATION_SENSORS:

        return LocalizationResult(
            success=False,
            x=None,
            y=None,
            z=None,
            sensors_used=sensor_count,
            message="Insufficient sensors for localization",
        )

    # Placeholder until localization algorithm is added
    return LocalizationResult(
        success=True,
        x=0.0,
        y=0.0,
        z=0.0,
        sensors_used=sensor_count,
        message="Localization successful",
    )


def analyze_trend(h1_result: H1Result) -> TrendResult:
    """
    Placeholder b-value trend analysis.
    """

    hit_count = len(h1_result.eligible_hits)

    if hit_count < 20:

        return TrendResult(
            b_value=None,
            trend="Insufficient Data",
            confidence=0,
        )

    return TrendResult(
        b_value=1.20,
        trend="Stable",
        confidence=80,
    )


def analyze_load_history() -> LoadHistoryResult:
    """
    Placeholder load-history analysis.
    """

    return LoadHistoryResult(
        calm_ratio=None,
        felicity_ratio=None,
        previous_peak_load=None,
        current_peak_load=None,
    )


def analyze_ae(h1_result: H1Result) -> H2Result:
    """
    Complete H-2 pipeline.
    """

    localization = localize_hits(h1_result)

    trend = analyze_trend(h1_result)

    load_history = analyze_load_history()

    return H2Result(
    localization=localization,
    trend=trend,
    load_history=load_history,

    total_hits=len(h1_result.raw_hits),
    eligible_hits=len(h1_result.eligible_hits),
)
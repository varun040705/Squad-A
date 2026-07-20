"""
aggregate_engine.py

Alternate Squad H entry point for inputs that provide only a single
rolled-up Acoustic_Emissions_levels reading per timestamp, rather than
individual per-sensor AE hits (sensor_id, duration, rise_time, energy,
counts, peak_frequency, quality_score).

Design note -- why this is a separate module and not a patch to AEHit:
AEHit is a strict schema for genuine hit-level AE data, and the rest of
Squad H (ae_h1 noise filtering, ae_h2 localization) depends on fields an
aggregate source structurally cannot supply. Inventing rise_time,
duration, sensor_id, etc. to force aggregate rows into an AEHit would
silently fabricate data -- exactly what the workplan's "never estimate,
flag instead" rule forbids. Instead, this module:

  1. Runs the real b-value trend-analysis math (the one H2 sub-analysis
     that only needs timestamp + amplitude, both of which this input
     genuinely has) by reusing squad_h.ae_h2's b-value computation --
     one source of truth for that math, not a reimplementation.
  2. Reports localization as unavailable, honestly: no sensor_id means no
     way to know which sensor recorded a reading, so there is no basis
     for triangulation. This is a different, more specific reason than
     the hit-level pipeline's "insufficient_sensors_for_localization."
  3. Reports load-history (calm/felicity ratio) and grade as undetermined
     unless the caller separately supplies real phase-labeled load
     samples -- a bare Acoustic_Emissions_levels column carries no
     loading/unloading/reloading phase information.

Author: Sai Varun
Project: OX1 - Squad H
"""

import pandas as pd

from squad_h.models import (
    AcousticEmissionContext,
    LocalizationResult,
    LoadHistoryResult,
    TrendResult,
    TrendType,
    H2Result,
    LoadSample,
)
from squad_h.ae_h2 import _compute_b_value, analyze_load_history
from squad_h.ae_h3 import build_context
from squad_h.config import (
    MIN_HITS_FOR_TREND,
    MIN_WINDOWS_FOR_TREND,
    B_VALUE_DECLINE_SLOPE_THRESHOLD,
)


class AggregateReading:
    """
    One timestamped Acoustic_Emissions_levels value. Deliberately NOT an
    AEHit -- it carries only what an aggregate-level source actually has
    (timestamp, amplitude), not the per-sensor hit fields AEHit requires.
    """

    __slots__ = ("timestamp", "amplitude")

    def __init__(self, timestamp: float, amplitude: float):
        self.timestamp = timestamp
        self.amplitude = amplitude


def load_aggregate_ae_readings(
    csv_path: str,
    timestamp_col: str = "Timestamp",
    level_col: str = "Acoustic_Emissions_levels",
) -> tuple[list[AggregateReading], int]:
    """
    Load one AE amplitude reading per row from a bridge monitoring CSV
    that reports a single rolled-up Acoustic_Emissions_levels value per
    timestamp (rather than individual sensor hits).

    Rows with a missing level are dropped rather than filled -- there is
    no legitimate value to fill a missing AE reading with.

    Returns (readings, dropped_row_count).
    """

    df = pd.read_csv(csv_path)

    before = len(df)
    df = df.dropna(subset=[level_col])
    dropped = before - len(df)

    timestamps = pd.to_datetime(df[timestamp_col])
    origin = timestamps.min()
    elapsed_seconds = (timestamps - origin).dt.total_seconds()

    readings = [
        AggregateReading(timestamp=float(t), amplitude=float(a))
        for t, a in zip(elapsed_seconds, df[level_col])
    ]

    return readings, dropped


def analyze_aggregate_trend(
    readings: list[AggregateReading],
    window_size_seconds: float = 86400,   # 1 day -- see module docstring note below
) -> TrendResult:
    """
    Same windowed b-value slope analysis as ae_h2.analyze_trend, adapted
    to operate on AggregateReading instead of AEHit. Reuses the exact
    same _compute_b_value math -- the Gutenberg-Richter analog only ever
    needed amplitude values, which this input genuinely provides.

    window_size_seconds is deliberately its own parameter here rather
    than squad_h.config.WINDOW_SIZE (60s): that constant is calibrated
    for real sensor-level AE monitoring, where many discrete hits can
    land inside one minute. This dataset samples once per minute, so a
    60s window would only ever contain 1 reading -- never enough to fit
    a per-window b-value. A wider window (1 day by default) gives enough
    readings per window to actually compute a trend.
    """

    if len(readings) < MIN_HITS_FOR_TREND:
        return TrendResult(b_value=None, trend=TrendType.INSUFFICIENT_DATA, confidence=0)

    min_t = min(r.timestamp for r in readings)
    windows: dict[int, list[AggregateReading]] = {}
    for r in readings:
        idx = int((r.timestamp - min_t) // window_size_seconds)
        windows.setdefault(idx, []).append(r)

    window_b_values = []
    for idx in sorted(windows.keys()):
        bv = _compute_b_value(windows[idx])
        if bv is not None:
            window_b_values.append(bv)

    if len(window_b_values) < MIN_WINDOWS_FOR_TREND:
        overall_bv = _compute_b_value(readings)
        return TrendResult(
            b_value=overall_bv,
            trend=TrendType.INSUFFICIENT_DATA,
            confidence=40 if overall_bv is not None else 0,
        )

    n = len(window_b_values)
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(window_b_values) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, window_b_values))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    slope = cov / var_x if var_x != 0 else 0.0

    if slope < B_VALUE_DECLINE_SLOPE_THRESHOLD:
        trend = TrendType.DECREASING
    elif slope > -B_VALUE_DECLINE_SLOPE_THRESHOLD:
        trend = TrendType.INCREASING
    else:
        trend = TrendType.STABLE

    return TrendResult(
        b_value=window_b_values[-1],
        trend=trend,
        confidence=min(90, 40 + n * 10),
    )


def run_aggregate_ae(
    inspection_id: str,
    element_ref: str,
    csv_path: str,
    timestamp_col: str = "Timestamp",
    level_col: str = "Acoustic_Emissions_levels",
    load_samples: list[LoadSample] | None = None,
    window_size_seconds: float = 86400,
) -> AcousticEmissionContext:
    """
    Complete Squad H pipeline for an aggregate-level source (e.g.
    bridge_digital_twin_dataset.csv), in place of run_ae_engine's
    per-hit AEHit input.

    load_samples is still accepted -- if the caller has genuine
    phase-labeled load-cell data from elsewhere, calm_ratio/felicity_ratio
    and grading can still be computed exactly as in the full hit-level
    pipeline. Without it, grade correctly stays undetermined rather than
    guessed.
    """

    readings, dropped = load_aggregate_ae_readings(csv_path, timestamp_col, level_col)

    flags = ["aggregate_input:no_per_sensor_hit_data"]
    if dropped:
        flags.append(f"rows_dropped_missing_level:{dropped}")

    localization = LocalizationResult(
        success=False,
        x=None, y=None, z=None,
        sensors_used=0,
        message="localization_unavailable:aggregate_input_has_no_sensor_id",
    )
    flags.append(localization.message)

    trend = analyze_aggregate_trend(readings, window_size_seconds=window_size_seconds)
    if trend.trend == TrendType.DECREASING:
        flags.append("b_value_declining")

    if load_samples:
        # analyze_load_history only ever needs something with a
        # .timestamp attribute for the eligible_hits it scans -- reuse
        # the real function rather than reimplementing it.
        class _EligibleHitsView:
            def __init__(self, eligible_hits):
                self.eligible_hits = eligible_hits

        load_history = analyze_load_history(_EligibleHitsView(readings), load_samples)
    else:
        load_history = LoadHistoryResult(
            calm_ratio=None, felicity_ratio=None,
            previous_peak_load=None, current_peak_load=None,
        )
        flags.append("load_history_unavailable:no_phase_labeled_load_samples_supplied")

    h2_result = H2Result(
        localization=localization,
        trend=trend,
        load_history=load_history,
        total_hits=len(readings),
        eligible_hits=len(readings),  # no noise-filtering possible on aggregate input
        flags=flags,
    )

    return build_context(inspection_id, element_ref, h2_result)


"""
ae_h2.py

H-2 : Localization and Trend Analysis

Author: Sai Varun
Project: OX1 - Squad H
"""

import math
from squad_h.models import (
    AEHit,
    H1Result,
    H2Result,
    LocalizationResult,
    TrendResult,
    LoadHistoryResult,
    TrendType,
    SensorGeometry,
    LoadSample,
    LoadPhase,
)

from squad_h.config import (
    MIN_LOCALIZATION_SENSORS,
    MIN_HITS_FOR_TREND,
    WINDOW_SIZE,
    MIN_WINDOWS_FOR_TREND,
    B_VALUE_DECLINE_SLOPE_THRESHOLD,
    DEFAULT_WAVE_VELOCITY_MPS,
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


def _triangulate_hit(
    hit_arrivals: dict[str, float],
    sensor_positions: dict[str, SensorGeometry],
    wave_velocity: float,
) -> tuple[float, float, float] | None:
    """
    Solve for source (x, y, z) from arrival-time differences across sensors,
    using the standard linearized TDOA approach: pick a reference sensor,
    subtract its equation from every other sensor's equation to cancel the
    quadratic source-position term, leaving a linear system solvable by
    least squares.

    hit_arrivals: {sensor_id: arrival_timestamp} for sensors that detected
                  this specific hit (>= MIN_LOCALIZATION_SENSORS required
                  by the caller before this is invoked).

    Returns None if the system is degenerate (e.g. sensors are coplanar
    for a 3D solve) -- caller must treat that as "insufficient geometry",
    NOT estimate a location anyway.
    """

    sensor_ids = list(hit_arrivals.keys())
    ref_id = sensor_ids[0]
    ref_pos = sensor_positions[ref_id]
    ref_t = hit_arrivals[ref_id]

    rows = []
    rhs = []

    for sid in sensor_ids[1:]:
        pos = sensor_positions[sid]
        dt = hit_arrivals[sid] - ref_t
        range_diff = wave_velocity * dt  # (distance_i - distance_ref)

        # Linearized TDOA equation coefficients (standard hyperbolic multilateration)
        a = 2 * (pos.x - ref_pos.x)
        b = 2 * (pos.y - ref_pos.y)
        c = 2 * (pos.z - ref_pos.z)
        d = (
            (pos.x**2 + pos.y**2 + pos.z**2)
            - (ref_pos.x**2 + ref_pos.y**2 + ref_pos.z**2)
            - range_diff**2
        )

        rows.append([a, b, c])
        rhs.append(d)

    # Solve the normal equations (A^T A) x = A^T b via plain Gaussian elimination
    # (no numpy dependency assumed) -- 3x3 system.
    try:
        ata = [[sum(rows[k][i] * rows[k][j] for k in range(len(rows))) for j in range(3)] for i in range(3)]
        atb = [sum(rows[k][i] * rhs[k] for k in range(len(rows))) for i in range(3)]

        det = (
            ata[0][0] * (ata[1][1] * ata[2][2] - ata[1][2] * ata[2][1])
            - ata[0][1] * (ata[1][0] * ata[2][2] - ata[1][2] * ata[2][0])
            + ata[0][2] * (ata[1][0] * ata[2][1] - ata[1][1] * ata[2][0])
        )
        if abs(det) < 1e-9:
            return None  # degenerate geometry -- do not estimate

        # Cramer's rule
        def solve_axis(col):
            m = [row[:] for row in ata]
            for i in range(3):
                m[i][col] = atb[i]
            d = (
                m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
                - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
                + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
            )
            return d / det

        x = solve_axis(0)
        y = solve_axis(1)
        z = solve_axis(2)
        return (x, y, z)
    except ZeroDivisionError:
        return None


def localize_hits(
    h1_result: H1Result,
    sensor_positions: dict[str, SensorGeometry] | None = None,
    wave_velocity: float = DEFAULT_WAVE_VELOCITY_MPS,
) -> LocalizationResult:
    """
    Perform source localization from arrival-time differences.

    Requires known sensor positions (element-specific -- passed by caller,
    since these depend on the actual sensor array layout for this element
    and can't be a global config constant). Without sensor_positions this
    falls back to sensor-count validation only and reports insufficient
    data, matching the "never estimate" rule.
    """

    sensor_count = validate_sensor_count(h1_result)

    if sensor_count < MIN_LOCALIZATION_SENSORS:
        return LocalizationResult(
            success=False,
            x=None,
            y=None,
            z=None,
            sensors_used=sensor_count,
            message="insufficient_sensors_for_localization",
        )

    if not sensor_positions:
        return LocalizationResult(
            success=False,
            x=None,
            y=None,
            z=None,
            sensors_used=sensor_count,
            message="sensor_positions_not_provided",
        )

    # Group hits by a common origin event using per-sensor arrival grouping.
    # Simplification: treat each eligible hit as its own event, keyed by
    # nearest-in-time hits across sensors within one WINDOW_SIZE. A fuller
    # event-association algorithm (cross-correlation matching) belongs here
    # eventually -- flagged rather than silently approximated.
    hits_by_sensor: dict[str, list[AEHit]] = {}
    for hit in h1_result.eligible_hits:
        hits_by_sensor.setdefault(hit.sensor_id, []).append(hit)

    all_sensors = list(hits_by_sensor.keys())
    if len(all_sensors) < MIN_LOCALIZATION_SENSORS:
        return LocalizationResult(
            success=False, x=None, y=None, z=None,
            sensors_used=len(all_sensors),
            message="insufficient_sensors_for_localization",
        )

    ref_sensor = all_sensors[0]
    ref_hit = hits_by_sensor[ref_sensor][0]

    arrivals = {ref_sensor: ref_hit.timestamp}
    for sid in all_sensors[1:]:
        nearest = min(hits_by_sensor[sid], key=lambda h: abs(h.timestamp - ref_hit.timestamp))
        arrivals[sid] = nearest.timestamp

    if len(arrivals) < MIN_LOCALIZATION_SENSORS:
        return LocalizationResult(
            success=False, x=None, y=None, z=None,
            sensors_used=len(arrivals),
            message="insufficient_sensors_for_localization",
        )

    missing = [sid for sid in arrivals if sid not in sensor_positions]
    if missing:
        return LocalizationResult(
            success=False, x=None, y=None, z=None,
            sensors_used=len(arrivals),
            message=f"missing_sensor_geometry:{','.join(missing)}",
        )

    result = _triangulate_hit(arrivals, sensor_positions, wave_velocity)
    if result is None:
        return LocalizationResult(
            success=False, x=None, y=None, z=None,
            sensors_used=len(arrivals),
            message="degenerate_sensor_geometry",
        )

    x, y, z = result
    return LocalizationResult(
        success=True,
        x=x, y=y, z=z,
        sensors_used=len(arrivals),
        message="Localization successful",
    )


def _compute_b_value(hits: list[AEHit]) -> float | None:
    """
    Fit the Gutenberg-Richter analog: log10(N) = a - b*M, where M is
    amplitude (dB) used as the AE magnitude proxy and N is the count of
    hits with amplitude >= M. Fit via simple linear least squares over
    1 dB bins.
    """

    if len(hits) < MIN_HITS_FOR_TREND:
        return None

    amplitudes = sorted(h.amplitude for h in hits)
    min_amp, max_amp = int(min(amplitudes)), int(max(amplitudes)) + 1

    xs, ys = [], []
    for m in range(min_amp, max_amp):
        n = sum(1 for a in amplitudes if a >= m)
        if n > 0:
            xs.append(m)
            ys.append(math.log10(n))

    if len(xs) < 2:
        return None

    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs)

    if var_x == 0:
        return None

    slope = cov / var_x  # this is -b in log10(N) = a - b*M
    b_value = -slope
    return b_value


def analyze_trend(h1_result: H1Result) -> TrendResult:
    """
    Real b-value trend analysis: bin eligible hits into WINDOW_SIZE-second
    windows by timestamp, compute a b-value per window, then fit the slope
    of b-value vs. window index. A slope more negative than
    B_VALUE_DECLINE_SLOPE_THRESHOLD => declining trend (growing severity).
    """

    hits = h1_result.eligible_hits

    if len(hits) < MIN_HITS_FOR_TREND:
        return TrendResult(b_value=None, trend=TrendType.INSUFFICIENT_DATA, confidence=0)

    min_t = min(h.timestamp for h in hits)
    windows: dict[int, list[AEHit]] = {}
    for h in hits:
        idx = int((h.timestamp - min_t) // WINDOW_SIZE)
        windows.setdefault(idx, []).append(h)

    window_b_values = []
    for idx in sorted(windows.keys()):
        bv = _compute_b_value(windows[idx])
        if bv is not None:
            window_b_values.append(bv)

    if len(window_b_values) < MIN_WINDOWS_FOR_TREND:
        # Not enough windows to call a trend -- but we can still report
        # an overall b-value for the whole eligible set.
        overall_bv = _compute_b_value(hits)
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
        confidence=min(90, 40 + n * 10),  # more windows -> more confidence, capped
    )


def analyze_load_history(
    h1_result: H1Result,
    load_samples: list[LoadSample] | None = None,
) -> LoadHistoryResult:
    """
    Calm ratio: AE hit activity during unloading, relative to prior loading.
    Felicity ratio: load at AE re-onset during reloading, over previous peak load.

    Requires a correlated load-cell stream (load_samples) -- without it
    there is no basis to compute either ratio, and this returns all-None
    rather than guessing.
    """

    if not load_samples:
        return LoadHistoryResult(
            calm_ratio=None,
            felicity_ratio=None,
            previous_peak_load=None,
            current_peak_load=None,
        )

    loading = [s for s in load_samples if s.phase == LoadPhase.LOADING]
    unloading = [s for s in load_samples if s.phase == LoadPhase.UNLOADING]
    reloading = [s for s in load_samples if s.phase == LoadPhase.RELOADING]

    previous_peak_load = max((s.load for s in loading), default=None)
    current_peak_load = max((s.load for s in load_samples), default=None)

    def _nearest_sample_load(t: float) -> float | None:
        if not load_samples:
            return None
        nearest = min(load_samples, key=lambda s: abs(s.timestamp - t))
        return nearest.load

    # Windows are defined by phase *transition* timestamps, not by the span
    # of samples belonging to one phase -- a phase can be marked by a
    # single sample (e.g. one "unloading started here" reading), and using
    # only that phase's own sample span would collapse the window to zero
    # width and silently undercount hits.
    loading_start = min((s.timestamp for s in loading), default=None)
    unloading_start = min((s.timestamp for s in unloading), default=None)
    reloading_start = min((s.timestamp for s in reloading), default=None)
    monitoring_end = max((s.timestamp for s in load_samples), default=None)

    def _count_hits_between(t0: float, t1: float) -> int:
        return sum(1 for h in h1_result.eligible_hits if t0 <= h.timestamp < t1)

    calm_ratio = None
    if loading_start is not None and unloading_start is not None:
        loading_window_end = unloading_start
        unloading_window_end = reloading_start if reloading_start is not None else monitoring_end

        loading_hits = _count_hits_between(loading_start, loading_window_end)
        unloading_hits = _count_hits_between(unloading_start, unloading_window_end + 1e-9)

        if loading_hits > 0:
            calm_ratio = unloading_hits / loading_hits

    felicity_ratio = None
    if reloading_start is not None and previous_peak_load:
        # Reloading is the last modeled phase here -- its window has no
        # upper bound from this data (a later loading cycle would need its
        # own transition sample to close it off).
        reloading_window_end = float("inf")
        reonset_hit = next(
            (h for h in sorted(h1_result.eligible_hits, key=lambda h: h.timestamp)
             if reloading_start <= h.timestamp < reloading_window_end),
            None,
        )
        if reonset_hit is not None:
            reonset_load = _nearest_sample_load(reonset_hit.timestamp)
            if reonset_load is not None:
                felicity_ratio = reonset_load / previous_peak_load

    return LoadHistoryResult(
        calm_ratio=calm_ratio,
        felicity_ratio=felicity_ratio,
        previous_peak_load=previous_peak_load,
        current_peak_load=current_peak_load,
    )


def analyze_ae(
    h1_result: H1Result,
    sensor_positions: dict[str, SensorGeometry] | None = None,
    wave_velocity: float = DEFAULT_WAVE_VELOCITY_MPS,
    load_samples: list[LoadSample] | None = None,
) -> H2Result:
    """
    Complete H-2 pipeline.
    """

    localization = localize_hits(h1_result, sensor_positions, wave_velocity)
    trend = analyze_trend(h1_result)
    load_history = analyze_load_history(h1_result, load_samples)

    flags = []
    if not localization.success:
        flags.append(localization.message)
    if trend.trend == TrendType.DECREASING:
        flags.append("b_value_declining")

    return H2Result(
        localization=localization,
        trend=trend,
        load_history=load_history,
        total_hits=len(h1_result.raw_hits),
        eligible_hits=len(h1_result.eligible_hits),
        flags=flags,
    )

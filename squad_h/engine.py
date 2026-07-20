from squad_h.ae_h1 import preprocess_and_detect_hits
from squad_h.ae_h2 import analyze_ae
from squad_h.ae_h3 import build_context
from squad_h.config import DEFAULT_WAVE_VELOCITY_MPS


def run_ae_engine(
    inspection_id: str,
    element_ref: str,
    hits,
    sensor_positions=None,
    wave_velocity: float = DEFAULT_WAVE_VELOCITY_MPS,
    load_samples=None,
):
    """
    Complete AE processing pipeline.

    sensor_positions: dict[sensor_id -> SensorGeometry], required for
        real triangulation (element-specific sensor array layout).
    load_samples: list[LoadSample], required for calm_ratio/felicity_ratio.
        Without these, localization and grading will correctly come back
        flagged as insufficient rather than estimated.
    """

    h1_result = preprocess_and_detect_hits(hits)

    h2_result = analyze_ae(
        h1_result,
        sensor_positions=sensor_positions,
        wave_velocity=wave_velocity,
        load_samples=load_samples,
    )

    context = build_context(
        inspection_id,
        element_ref,
        h2_result,
    )

    return context

"""
test_h2.py
"""
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from squad_h.models import AEHit, SensorGeometry, LoadSample, LoadPhase
from squad_h.ae_h1 import preprocess_and_detect_hits
from squad_h.ae_h2 import analyze_ae


def test_localization_requires_four_sensors():

    hits = [

        AEHit(
            sensor_id="S1",
            timestamp=0.1,
            amplitude=40,
            duration=1,
            energy=50,
            rise_time=0.5,
            counts=20,
            peak_frequency=200,
            quality_score=95,
        )
    ]

    h1 = preprocess_and_detect_hits(hits)

    h2 = analyze_ae(h1)

    assert h2.localization.success is False
    assert h2.localization.sensors_used == 1
    assert "insufficient_sensors_for_localization" in h2.flags


def test_localization_without_sensor_positions_flags_not_estimates():
    # 4+ sensors detect the hit, but no geometry is supplied -- must NOT
    # fabricate a location.

    hits = [
        AEHit(sensor_id=f"S{i}", timestamp=0.1 + i * 0.001, amplitude=40,
              duration=1, energy=50, rise_time=0.2, counts=20,
              peak_frequency=200, quality_score=95)
        for i in range(1, 5)
    ]

    h1 = preprocess_and_detect_hits(hits)
    h2 = analyze_ae(h1)  # no sensor_positions passed

    assert h2.localization.success is False
    assert h2.localization.message == "sensor_positions_not_provided"


def test_localization_triangulates_with_known_geometry():
    # NOTE: sensors must NOT be coplanar for a 3D solve -- an all-z=0
    # layout leaves the z-column of the linear system all zeros (singular),
    # which is correctly caught as degenerate_sensor_geometry rather than
    # producing a fabricated location. S4 is placed off-plane here.
    sensor_positions = {
        "S1": SensorGeometry(sensor_id="S1", x=0.0, y=0.0, z=0.0),
        "S2": SensorGeometry(sensor_id="S2", x=1.0, y=0.0, z=0.0),
        "S3": SensorGeometry(sensor_id="S3", x=0.0, y=1.0, z=0.0),
        "S4": SensorGeometry(sensor_id="S4", x=1.0, y=1.0, z=1.0),
    }

    hits = [
        AEHit(sensor_id=f"S{i}", timestamp=0.1 + i * 0.0001, amplitude=40,
              duration=1, energy=50, rise_time=0.2, counts=20,
              peak_frequency=200, quality_score=95)
        for i in range(1, 5)
    ]

    h1 = preprocess_and_detect_hits(hits)
    h2 = analyze_ae(h1, sensor_positions=sensor_positions)

    assert h2.localization.success is True
    assert h2.localization.x is not None


def test_localization_flags_degenerate_coplanar_geometry():
    # A purely 2D (coplanar) sensor array cannot resolve a 3D position --
    # this must be flagged, not silently return a bogus z.

    sensor_positions = {
        "S1": SensorGeometry(sensor_id="S1", x=0.0, y=0.0, z=0.0),
        "S2": SensorGeometry(sensor_id="S2", x=1.0, y=0.0, z=0.0),
        "S3": SensorGeometry(sensor_id="S3", x=0.0, y=1.0, z=0.0),
        "S4": SensorGeometry(sensor_id="S4", x=1.0, y=1.0, z=0.0),
    }

    hits = [
        AEHit(sensor_id=f"S{i}", timestamp=0.1 + i * 0.0001, amplitude=40,
              duration=1, energy=50, rise_time=0.2, counts=20,
              peak_frequency=200, quality_score=95)
        for i in range(1, 5)
    ]

    h1 = preprocess_and_detect_hits(hits)
    h2 = analyze_ae(h1, sensor_positions=sensor_positions)

    assert h2.localization.success is False
    assert h2.localization.message == "degenerate_sensor_geometry"


def test_load_history_requires_load_samples():

    hits = [
        AEHit(sensor_id="S1", timestamp=0.1, amplitude=40, duration=1,
              energy=50, rise_time=0.2, counts=20, peak_frequency=200,
              quality_score=95)
    ]

    h1 = preprocess_and_detect_hits(hits)
    h2 = analyze_ae(h1)  # no load_samples passed

    assert h2.load_history.calm_ratio is None
    assert h2.load_history.felicity_ratio is None


def test_load_history_computes_calm_and_felicity_ratio():

    hits = [
        AEHit(sensor_id="S1", timestamp=0.1, amplitude=40, duration=1,
              energy=50, rise_time=0.2, counts=20, peak_frequency=200,
              quality_score=95),
        AEHit(sensor_id="S1", timestamp=0.3, amplitude=40, duration=1,
              energy=50, rise_time=0.2, counts=20, peak_frequency=200,
              quality_score=95),
        AEHit(sensor_id="S1", timestamp=0.5, amplitude=40, duration=1,
              energy=50, rise_time=0.2, counts=20, peak_frequency=200,
              quality_score=95),
    ]

    load_samples = [
        LoadSample(timestamp=0.0, load=100.0, phase=LoadPhase.LOADING),
        LoadSample(timestamp=0.2, load=150.0, phase=LoadPhase.UNLOADING),
        LoadSample(timestamp=0.4, load=120.0, phase=LoadPhase.RELOADING),
    ]

    h1 = preprocess_and_detect_hits(hits)
    h2 = analyze_ae(h1, load_samples=load_samples)

    assert h2.load_history.previous_peak_load == 100.0
    assert h2.load_history.calm_ratio is not None
    assert h2.load_history.felicity_ratio is not None


if __name__ == "__main__":
    test_localization_requires_four_sensors()
    test_localization_without_sensor_positions_flags_not_estimates()
    test_localization_triangulates_with_known_geometry()
    test_localization_flags_degenerate_coplanar_geometry()
    test_load_history_requires_load_samples()
    test_load_history_computes_calm_and_felicity_ratio()
    print("✓ test_h2 passed")
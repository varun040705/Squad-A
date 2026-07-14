"""
test_h2.py
"""
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from squad_h.models import AEHit
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
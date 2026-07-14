"""
test_engine.py
"""
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from squad_h.models import AEHit
from squad_h.engine import run_ae_engine


def test_complete_pipeline():

    hits = [

        AEHit(
            sensor_id="S1",
            timestamp=0.1,
            amplitude=45,
            duration=1,
            energy=50,
            rise_time=0.4,
            counts=15,
            peak_frequency=220,
            quality_score=95,
        )
    ]

    context = run_ae_engine(
        "AE-001",
        hits,
    )

    assert context.inspection_id == "AE-001"
    assert context.total_hits == 1
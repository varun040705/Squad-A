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
        inspection_id="AE-001",
        element_ref="C-07",
        hits=hits,
    )

    assert context.inspection_id == "AE-001"
    assert context.element_ref == "C-07"
    assert context.hits_total == 1
    assert context.grade is None  # no sensor_positions/load_samples supplied
    assert "grade_undetermined" in context.flags


if __name__ == "__main__":
    test_complete_pipeline()
    print("✓ test_engine passed")
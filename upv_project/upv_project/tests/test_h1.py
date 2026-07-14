"""
test_h1.py

Tests for H-1 preprocessing.
"""
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from squad_h.models import AEHit
from squad_h.ae_h1 import preprocess_and_detect_hits


def test_noise_filter():

    hits = [

        AEHit(
            sensor_id="S1",
            timestamp=0.1,
            amplitude=50,
            duration=1,
            energy=40,
            rise_time=0.5,
            counts=20,
            peak_frequency=250,
            quality_score=95,
        ),

        AEHit(
            sensor_id="S2",
            timestamp=0.2,
            amplitude=5,
            duration=1,
            energy=2,
            rise_time=0.3,
            counts=1,
            peak_frequency=100,
            quality_score=80,
        ),
    ]

    result = preprocess_and_detect_hits(hits)

    assert len(result.raw_hits) == 2
    assert len(result.eligible_hits) == 1
    assert result.raw_hits[1].is_noise
    
if __name__ == "__main__":
    test_noise_filter()
    print("✓ test_noise_filter passed")
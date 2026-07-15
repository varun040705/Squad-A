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
    # rise_time / duration > 0.5 => noise, per workplan H-1.

    hits = [

        AEHit(
            sensor_id="S1",
            timestamp=0.1,
            amplitude=50,
            duration=1,
            energy=40,
            rise_time=0.3,      # ratio 0.3 -> genuine AE hit
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
            rise_time=0.7,      # ratio 0.7 -> noise
            counts=1,
            peak_frequency=100,
            quality_score=80,
        ),
    ]

    result = preprocess_and_detect_hits(hits)

    assert len(result.raw_hits) == 2       # noise is retained, never deleted
    assert len(result.eligible_hits) == 1  # only the non-noise hit is eligible
    assert result.raw_hits[1].is_noise
    assert "noise_hits_excluded:1" in result.flags


def test_zero_duration_treated_as_noise():
    # duration == 0 can't produce a ratio -- must be flagged, not divide-by-zero.

    hit = AEHit(
        sensor_id="S1", timestamp=0.1, amplitude=50, duration=0,
        energy=40, rise_time=0.0, counts=20, peak_frequency=250,
        quality_score=95,
    )

    result = preprocess_and_detect_hits([hit])

    assert result.raw_hits[0].is_noise
    assert len(result.eligible_hits) == 0


if __name__ == "__main__":
    test_noise_filter()
    test_zero_duration_treated_as_noise()
    print("✓ test_h1 passed")
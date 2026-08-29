import pytest
from modules.dimensional.inspection import run_dimensional_engine, FlatnessClassification

def test_cover_qa_and_astm_e1155_flatness():
    payload = {
        "element_ref": "SLAB-01",
        "nominal_cover_mm": 40.0,
        "measured_covers_mm": [38.0, 41.0, 39.0, 42.0, 35.0, 40.0],
        "elevation_readings_mm": [0.0, 2.0, 1.0, 3.0, 2.0, 4.0, 3.0, 5.0]
    }
    result = run_dimensional_engine(payload)
    assert not result.has_errors
    assert result.mean_cover_mm == 39.2
    assert result.cover_compliance_pct == 100.0
    assert result.ff_flatness_number is not None
    assert result.fl_levelness_number is not None

def test_cover_out_of_tolerance():
    payload = {
        "element_ref": "WALL-02",
        "nominal_cover_mm": 40.0,
        "measured_covers_mm": [25.0, 40.0, 42.0] # 25mm is below (40-10)=30mm ACI 117 limit
    }
    result = run_dimensional_engine(payload)
    assert not result.has_errors
    assert result.flags.cover_out_of_tolerance
    assert result.cover_compliance_pct < 100.0

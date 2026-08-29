import pytest
from modules.ndt.rebound_upv import run_ndt_engine, ConcreteQualityClass

def test_rebound_hammer_outlier_filtering():
    # 10 readings where 1 is an extreme outlier (> 6 units from mean)
    # Mean of 30, 32, 31, 30, 31, 32, 30, 31, 30, 48 is 33.6
    # 48 differs from 33.6 by 14.4 (> 6.0), so 48 is discarded!
    readings = [30.0, 32.0, 31.0, 30.0, 31.0, 32.0, 30.0, 31.0, 30.0, 48.0]
    payload = {
        "element_ref": "COL-01",
        "rebound_readings": readings,
        "impact_angle": "horizontal"
    }
    result = run_ndt_engine(payload)
    assert not result.has_errors
    assert result.discarded_outliers_count == 1
    assert result.filtered_rebound_average == 30.78
    assert result.estimated_fc_mpa > 20.0

def test_upv_wave_velocity():
    payload = {
        "element_ref": "BEAM-02",
        "rebound_readings": [35.0] * 10,
        "distance_m": 0.4,
        "transit_time_us": 95.0 # 0.4 * 1e6 / 95 = 4210.5 m/s -> Good
    }
    result = run_ndt_engine(payload)
    assert not result.has_errors
    assert result.pulse_velocity_m_s == 4210.5
    assert result.concrete_quality == ConcreteQualityClass.good
    assert result.sonreb_combined_fc_mpa is not None

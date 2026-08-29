import pytest
from modules.shm.monitoring import run_shm_engine, ThermalRiskLevel, StressYieldStatus

def test_shm_thermal_and_stress_strain():
    payload = {
        "element_ref": "MASS-POUR-01",
        "core_temp_c": 55.0,
        "surface_temp_c": 30.0, # Delta T = 25°C (> 20°C limit -> High risk)
        "measured_microstrain": 500.0, # 500 ue
        "elastic_modulus_gpa": 30.0, # 30 GPa -> sigma = 15.0 MPa
        "yield_strength_mpa": 30.0 # 15/30 = 50% -> Safe
    }
    result = run_shm_engine(payload)
    assert not result.has_errors
    assert result.thermal_differential_dt_c == 25.0
    assert result.thermal_risk == ThermalRiskLevel.high
    assert result.flags.exceeds_thermal_limit
    assert result.calculated_stress_mpa == 15.0
    assert result.yield_ratio_pct == 50.0
    assert result.yield_status == StressYieldStatus.safe

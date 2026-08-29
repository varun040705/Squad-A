import pytest
from modules.geotechnical.qa import run_geotechnical_engine, SoilDensityClass

def test_spt_n60_and_terzaghi_bearing():
    payload = {
        "element_ref": "FOOTING-F1",
        "raw_spt_n": 18,
        "energy_ratio_ce": 0.80, # Auto hammer
        "footing_width_b_m": 2.0,
        "footing_depth_df_m": 1.5,
        "soil_cohesion_c_kpa": 15.0,
        "soil_friction_phi_deg": 32.0,
        "soil_unit_weight_gamma_kn_m3": 19.0,
        "footing_shape": "square"
    }
    result = run_geotechnical_engine(payload)
    assert not result.has_errors
    assert result.corrected_spt_n60 > 18.0
    assert result.soil_density_class == SoilDensityClass.medium_dense
    assert result.terzaghi_ult_bearing_kpa > 500.0
    assert result.allowable_bearing_kpa > 150.0

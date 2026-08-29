import pytest
from modules.forensics.investigation import run_forensics_engine, DepassivationRisk

def test_carbonation_and_chloride_ingress():
    payload = {
        "element_ref": "BRIDGE-DECK-B",
        "service_age_years": 25.0,
        "cover_depth_mm": 40.0,
        "carbonation_depth_mm": 15.0, # k = 15 / 5 = 3.0 mm/year^0.5
        "surface_chloride_cs_pct": 0.6,
        "diffusion_coeff_d_m2s": 1e-12,
        "threshold_chloride_ct_pct": 0.05
    }
    result = run_forensics_engine(payload)
    assert not result.has_errors
    assert result.carbonation_coefficient_k == 3.0
    assert result.time_to_carbonation_depassivation_years > 50.0
    assert result.chloride_at_rebar_pct is not None

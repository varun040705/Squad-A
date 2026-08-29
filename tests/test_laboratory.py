import pytest
from modules.laboratory.testing import run_laboratory_engine, ACI318Compliance

def test_compressive_and_split_tensile():
    payload = {
        "element_ref": "CYLINDER-28D",
        "specified_fc_mpa": 30.0,
        "cylinder_diameter_mm": 150.0,
        "cylinder_length_mm": 300.0,
        "compressive_loads_kn": [600.0, 620.0, 610.0], # ~ 34.5 MPa
        "split_tensile_loads_kn": [250.0, 260.0]
    }
    result = run_laboratory_engine(payload)
    assert not result.has_errors
    assert result.mean_compressive_fc_mpa > 34.0
    assert result.aci318_status == ACI318Compliance.passed
    assert result.mean_split_tensile_ft_mpa is not None

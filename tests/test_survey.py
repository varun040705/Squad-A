import pytest
from modules.survey.qa import run_survey_engine, PlumbnessStatus, SettlementAlertLevel

def test_survey_plumbness_and_settlement():
    payload = {
        "element_ref": "TOWER-NORTH",
        "height_m": 30.0,
        "top_offset_x_mm": 20.0,
        "top_offset_y_mm": 15.0, # Resultant drift = 25.0 mm. Allowable = min(30000/500, 150) = 60mm
        "settlement_history": [
            {"day": 0, "settlement_mm": 0.0},
            {"day": 30, "settlement_mm": 2.5},
            {"day": 60, "settlement_mm": 5.0}
        ]
    }
    result = run_survey_engine(payload)
    assert not result.has_errors
    assert result.resultant_drift_mm == 25.0
    assert result.plumbness_status == PlumbnessStatus.compliant
    assert result.total_settlement_mm == 5.0
    assert result.settlement_alert == SettlementAlertLevel.warning

import pytest
from squad_v.vi_v1 import VisualContextEngine

def test_calibration_perfect_conditions():
    calibrator = VisualContextEngine()
    result = calibrator.process_context(
        element_type="COLUMN",
        raw_width_mm=1.0,
        lighting_condition="STANDARD",
        accessibility_mode="DIRECT"
    )
    assert result["success"] is True
    assert result["corrected_crack_width_mm"] == 1.0
    # Your engine caps perfect conditions at 95% confidence
    assert result["confidence_ceiling"] == 95

def test_calibration_with_penalties():
    calibrator = VisualContextEngine()
    result = calibrator.process_context(
        element_type="COLUMN",
        raw_width_mm=2.0,
        lighting_condition="DUSTY_SURFACE",
        accessibility_mode="REMOTE_DRONE"
    )
    assert result["success"] is True
    assert round(result["corrected_crack_width_mm"], 2) == 2.40
    assert result["confidence_ceiling"] == 65
    assert "remote_drone_capture_active" in result["flags"]

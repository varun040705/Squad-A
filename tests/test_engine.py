import pytest
from squad_v.engine import VisualInspectionEngine

def test_full_pipeline_integration():
    engine = VisualInspectionEngine()
    grid_points = [
        {"id": "P1", "width_mm": 2.5, "surface_roughness_index": 0.8},
        {"id": "P2", "width_mm": 2.8, "surface_roughness_index": 0.9}
    ]

    output = engine.execute_pipeline(
        raw_width=2.5,
        element_type="COLUMN",
        lighting="DUSTY_SURFACE",
        access="REMOTE_DRONE",
        grid_points=grid_points
    )

    assert output["context"]["success"] is True
    # Verifies the pipeline passed the corrected width across modules
    assert output["context"]["corrected_crack_width_mm"] == 3.0
    assert output["grade"] == "CRITICAL / POOR"

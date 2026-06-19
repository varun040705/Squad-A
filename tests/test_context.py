"""
Unit Tests for UPV Context Engine - Segment A-1: Moisture & Mode Correction Module
"""

import pytest
from uuid import uuid4
from pydantic import ValidationError

from modules.upv.context import (
    apply_moisture_correction,
    apply_moisture_and_mode_corrections,
    assemble_context,
    UPVInputReading
)


# =====================================================================
# COMPONENT TESTS
# =====================================================================

def test_moisture_correction():
    """
    Checks that applying moisture correction gives correct factor and value.
    - Wet concrete (reduction of -18%)
    - Dry concrete (0%)
    - Slightly damp (-4%)
    - Damp (-9%)
    - Saturated (-25%)
    """
    # Test Wet: 4.5 * 0.82 = 3.6900
    vel_wet, log_wet = apply_moisture_correction(4.5, "wet")
    assert vel_wet == 3.6900
    assert log_wet is not None
    assert log_wet.type == "moisture"
    assert log_wet.factor == -0.18
    assert log_wet.reason == "wet condition"

    # Test Dry: 3.0 * 1.0 = 3.0000
    vel_dry, log_dry = apply_moisture_correction(3.0, "dry")
    assert vel_dry == 3.0000
    assert log_dry is None

    # Test Slightly Damp: 4.5 * 0.96 = 4.3200
    vel_sd, log_sd = apply_moisture_correction(4.5, "slightly_damp")
    assert vel_sd == 4.3200
    assert log_sd.factor == -0.04


def test_moisture_and_mode_corrections():
    """
    Verifies sequential application of corrections (moisture first, then mode penalty)
    and confidence ceiling effects.
    - Raw 4.5 km/s, wet, indirect
      1. Moisture wet (-18%): 4.5 * 0.82 = 3.69
      2. Mode indirect (-13%): 3.69 * 0.87 = 3.2103
      3. Ceiling: 60
    """
    vel_corrected, logs, ceiling = apply_moisture_and_mode_corrections(
        raw_velocity=4.5,
        moisture_condition="wet",
        transmission_mode="indirect"
    )
    assert vel_corrected == 3.2103
    assert len(logs) == 2
    assert logs[0].type == "moisture"
    assert logs[0].factor == -0.18
    assert logs[1].type == "mode"
    assert logs[1].factor == -0.13
    assert logs[1].reason == "indirect transmission"
    assert ceiling == 60


# =====================================================================
# INTEGRATED PIPELINE TESTS (assemble_context)
# =====================================================================

def test_pipeline_acceptance_test_1():
    """
    Acceptance Test 1:
    - raw=4.5, condition=wet, mode=direct
    - Expected output: corrected = 3.6900 km/s, ceiling = 100
    """
    elem_id = uuid4()
    input_data = {
        "element_id": elem_id,
        "raw_velocity_kmps": 4.5,
        "moisture_condition": "wet",
        "transmission_mode": "direct"
    }

    result = assemble_context(input_data)

    assert result.element_id == elem_id
    assert result.raw_velocity_kmps == 4.5
    assert result.moisture_corrected_velocity == 3.6900
    assert len(result.corrections_applied) == 1
    assert result.corrections_applied[0].type == "moisture"
    assert result.corrections_applied[0].factor == -0.18
    assert result.corrections_applied[0].reason == "wet condition"
    assert result.confidence_ceiling == 100


def test_pipeline_acceptance_test_2():
    """
    Acceptance Test 2:
    - raw=3.0, condition=dry, mode=direct
    - Expected output: corrected = 3.0000 km/s (no change), 0 corrections logged
    """
    elem_id = uuid4()
    input_data = {
        "element_id": elem_id,
        "raw_velocity_kmps": 3.0,
        "moisture_condition": "dry",
        "transmission_mode": "direct"
    }

    result = assemble_context(input_data)

    assert result.moisture_corrected_velocity == 3.0000
    assert len(result.corrections_applied) == 0
    assert result.confidence_ceiling == 100


def test_pipeline_acceptance_test_3():
    """
    Acceptance Test 3:
    - raw=5.0, condition=saturated, mode=direct
    - Expected output: corrected = 3.7500 km/s
    """
    elem_id = uuid4()
    input_data = {
        "element_id": elem_id,
        "raw_velocity_kmps": 5.0,
        "moisture_condition": "saturated",
        "transmission_mode": "direct"
    }

    result = assemble_context(input_data)

    assert result.moisture_corrected_velocity == 3.7500
    assert len(result.corrections_applied) == 1
    assert result.corrections_applied[0].type == "moisture"
    assert result.corrections_applied[0].factor == -0.25
    assert result.corrections_applied[0].reason == "saturated condition"


# =====================================================================
# SCHEMA VALIDATION & STRICT ERROR HANDLING TESTS
# =====================================================================

def test_validation_invalid_moisture():
    """
    Checks that unknown moisture condition raises a clear validation error.
    """
    with pytest.raises(ValidationError) as excinfo:
        UPVInputReading(
            element_id=uuid4(),
            raw_velocity_kmps=4.5,
            moisture_condition="very_wet",  # Invalid
            transmission_mode="direct"
        )
    assert "Unknown moisture condition 'very_wet'" in str(excinfo.value)


def test_validation_invalid_mode():
    """
    Checks that unknown transmission mode raises a clear validation error.
    """
    with pytest.raises(ValidationError) as excinfo:
        UPVInputReading(
            element_id=uuid4(),
            raw_velocity_kmps=4.5,
            moisture_condition="wet",
            transmission_mode="cross_hole"  # Invalid
        )
    assert "Unknown transmission mode 'cross_hole'" in str(excinfo.value)


def test_validation_invalid_velocity():
    """
    Checks that negative or zero velocity fails input validation.
    """
    with pytest.raises(ValidationError) as excinfo:
        UPVInputReading(
            element_id=uuid4(),
            raw_velocity_kmps=-1.2,
            moisture_condition="dry",
            transmission_mode="direct"
        )
    assert "Raw velocity must be positive" in str(excinfo.value)

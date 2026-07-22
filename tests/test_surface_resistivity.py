import pytest
from modules.electric.surface_resistivity import (
    run_resistivity_engine,
    calculate_average,
    calculate_cov,
    convert_to_celsius,
    CuringMethod,
    ElectrodeType,
    ChlorideRisk,
    CorrosionRisk,
    SurfaceResistivityInput
)

def test_calculate_average():
    assert calculate_average([10.0, 20.0, 30.0]) == 20.0
    assert calculate_average([]) is None


def test_calculate_cov():
    # Mean of 10, 10, 10 is 10, variance is 0, cov is 0
    assert calculate_cov([10.0, 10.0, 10.0], 10.0) == 0.0
    # Values: [8.0, 12.0], mean = 10.0, variance = ((8-10)^2 + (12-10)^2)/(2-1) = 8.0, std = sqrt(8) ~ 2.8284, cov = 2.8284 / 10 = 0.28284
    assert round(calculate_cov([8.0, 12.0], 10.0), 4) == 0.2828


def test_convert_to_celsius():
    assert convert_to_celsius(20.0, "C") == 20.0
    assert convert_to_celsius(68.0, "F") == 20.0  # (68-32)*5/9 = 20


def test_run_resistivity_engine_lime_water_arrhenius():
    # Saturated lime water cured concrete, tested at 25°C, corrected to 20°C
    raw_input = {
        "element_ref": "BEAM-01",
        "readings": [35.0] * 8, # Raw average is 35.0 kΩ-cm
        "temperature": 25.0,
        "temperature_unit": "C",
        "reference_temperature": 20.0,
        "correction_method": "arrhenius",
        "curing_method": "lime_water",
        "half_cell_readings": [-150.0, -180.0, -160.0], # Avg: -163.3 (Low risk)
        "electrode_type": "CSE"
    }
    
    result = run_resistivity_engine(raw_input)
    
    assert not result.has_errors
    assert result.measured_average == 35.0
    
    # Raw avg = 35.0. 
    # Curing correction (lime water) = 35.0 * 1.1 = 38.5 kΩ-cm.
    # Arrhenius temperature correction from 25°C (298.15K) to 20°C (293.15K):
    # exp( (28000 / 8.314) * ( (1/293.15) - (1/298.15) ) )
    # exp( 3367.81 * ( 0.00341122 - 0.00335401 ) ) = exp(3367.81 * 0.00005721) = exp(0.1926) ~ 1.2124
    # Final corrected resistivity = 38.5 * 1.2124 ~ 46.68 kΩ-cm.
    assert result.corrected_resistivity > 45.0
    assert result.corrected_resistivity < 48.0
    assert result.chloride_risk == ChlorideRisk.low # 37 to 254 is Low penetrability / risk
    assert result.half_cell_average == -163.3
    assert result.corrosion_risk == CorrosionRisk.low # > -200 mV is Low
    
    # Deductions: None. High readings count (8 >= 8), low COV (0.0), temp is 25°C (in standard range 15-25), half-cell count is 3 (>= 3), corrosion is low.
    assert result.confidence_ceiling == 100


def test_run_resistivity_engine_linear_moist_room():
    # Moist room cured, tested at 15°C, corrected to 20°C using linear model
    raw_input = {
        "element_ref": "COL-03",
        "readings": [18.0, 19.0, 20.0, 18.0, 19.0, 20.0, 18.0, 20.0], # Avg = 19.0
        "temperature": 15.0,
        "temperature_unit": "C",
        "reference_temperature": 20.0,
        "correction_method": "linear",
        "linear_coefficient": 0.02, # 2.0% per °C
        "curing_method": "moist_room",
        "half_cell_readings": [-400.0, -380.0, -420.0], # Avg: -400.0 (High risk)
        "electrode_type": "CSE"
    }
    
    result = run_resistivity_engine(raw_input)
    
    assert not result.has_errors
    assert result.measured_average == 19.0
    # Curing correction = 19.0 * 1.0 = 19.0
    # Linear temp correction factor = 1 + 0.02 * (15 - 20) = 1 + 0.02 * (-5) = 1 - 0.10 = 0.90
    # Final corrected resistivity = 19.0 * 0.90 = 17.10
    assert result.corrected_resistivity == 17.10
    assert result.chloride_risk == ChlorideRisk.high # 10 to 20 is High penetrability / risk
    assert result.corrosion_risk == CorrosionRisk.high # < -350 mV is High


def test_insufficient_data_flags():
    # 1. Missing temperature (blocked)
    raw_input = {
        "element_ref": "PIER-02",
        "readings": [25.0] * 8,
        "temperature": None,
        "curing_method": "moist_room"
    }
    
    result = run_resistivity_engine(raw_input)
    assert result.has_errors
    assert result.flags.missing_temperature
    assert result.corrected_resistivity is None
    assert result.chloride_risk is None
    assert result.confidence_ceiling == 0

    # 2. No readings at all (blocked)
    raw_input = {
        "element_ref": "PIER-02",
        "readings": [],
        "temperature": 20.0,
        "curing_method": "moist_room"
    }
    
    result = run_resistivity_engine(raw_input)
    assert result.has_errors
    assert result.flags.no_resistivity_data
    assert result.confidence_ceiling == 0

    # 3. Warning: insufficient count (< 8 readings) and few half cell (< 3 readings)
    raw_input = {
        "element_ref": "PIER-02",
        "readings": [25.0] * 5, # 5 is < 8
        "temperature": 20.0,
        "curing_method": "moist_room",
        "half_cell_readings": [-250.0], # 1 is < 3
        "electrode_type": "CSE"
    }
    
    result = run_resistivity_engine(raw_input)
    assert not result.has_errors
    assert result.flags.insufficient_resistivity_readings
    assert result.flags.insufficient_half_cell_readings
    # Confidence ceiling deductions:
    # Start: 100
    # -20 (fewer than 8 resistivity)
    # -20 (fewer than 3 half-cell)
    # -15 (corrosion risk is -250mV -> uncertain)
    # Expected confidence: 100 - 20 - 20 - 15 = 45
    assert result.confidence_ceiling == 45


def test_high_variance_flag():
    # Coefficient of variation > 15%
    raw_input = {
        "element_ref": "PIER-03",
        "readings": [10.0, 15.0, 25.0, 12.0, 18.0, 22.0, 11.0, 14.0], # Mean: 16.125, Std dev: 5.436, COV ~ 33.7% (> 15%)
        "temperature": 20.0,
        "curing_method": "moist_room"
    }
    
    result = run_resistivity_engine(raw_input)
    assert not result.has_errors
    assert result.flags.high_resistivity_variance
    # Confidence deductions:
    # Start: 100
    # -15 (COV > 10%)
    # Expected confidence: 100 - 15 = 85
    assert result.confidence_ceiling == 85


def test_electrode_classification_shift():
    # Saturated Calomel Electrode (SCE) test
    # Calomel bounds: > -120 mV (low), -120 to -270 mV (uncertain), < -270 mV (high)
    
    # 1. SCE -200 mV (Uncertain range for Calomel, but High range for CSE)
    raw_input = {
        "element_ref": "PIER-04",
        "readings": [30.0] * 8,
        "temperature": 20.0,
        "half_cell_readings": [-200.0] * 3,
        "electrode_type": "Calomel"
    }
    result = run_resistivity_engine(raw_input)
    assert result.corrosion_risk == CorrosionRisk.uncertain

    # 2. AgCl -260 mV (High range for AgCl, since boundary is < -250 mV)
    raw_input = {
        "element_ref": "PIER-04",
        "readings": [30.0] * 8,
        "temperature": 20.0,
        "half_cell_readings": [-260.0] * 3,
        "electrode_type": "AgCl"
    }
    result = run_resistivity_engine(raw_input)
    assert result.corrosion_risk == CorrosionRisk.high

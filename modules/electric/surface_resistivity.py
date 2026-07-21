"""
OX1 NDT Platform - Electric Module
Squad A - Segment E-1: Surface Resistivity & Corrosion Risk Context Engine

This module:
1. Performs temperature and curing corrections for concrete surface resistivity.
2. Interprets chloride permeability risk (AASHTO T 358) and half-cell corrosion risk (ASTM C876).
3. Analyzes reading variability and computes a dynamic confidence ceiling.
4. Enforces data completeness and flags insufficient data.
"""

import math
from typing import List, Optional, Dict
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator

# =====================================================================
# ENUMS & CONSTANTS
# =====================================================================

class CuringMethod(str, Enum):
    lime_water = "lime_water"
    moist_room = "moist_room"
    other = "other"


class ElectrodeType(str, Enum):
    CSE = "CSE"          # Copper-Copper Sulfate Electrode
    Calomel = "Calomel"  # Saturated Calomel Electrode
    AgCl = "AgCl"        # Silver-Silver Chloride Electrode


class ChlorideRisk(str, Enum):
    very_low = "very_low"
    low = "low"
    moderate = "moderate"
    high = "high"
    very_high = "very_high"


class CorrosionRisk(str, Enum):
    low = "low"
    uncertain = "uncertain"
    high = "high"


# Curing correction factors (AASHTO T 358)
# Saturated concrete cured in lime water is multiplied by 1.1 to convert to standard moist-cured equivalent.
CURING_FACTORS = {
    CuringMethod.lime_water: 1.1,
    CuringMethod.moist_room: 1.0,
    CuringMethod.other: 1.0,
}

# Gas constant R in J/(mol·K)
R_GAS_CONSTANT = 8.314

# Standard activation energy for electrical conduction in concrete (J/mol)
DEFAULT_ACTIVATION_ENERGY = 28000.0

# Standard linear temperature correction coefficient (% per °C)
# Saturated concrete averages 2.0% per °C change in resistivity.
DEFAULT_LINEAR_COEFFICIENT = 0.02


# =====================================================================
# PYDANTIC SCHEMAS
# =====================================================================

class CorrectionLogEntry(BaseModel):
    """
    Log of corrections applied to resistivity readings.
    """
    type: str = Field(..., description="Type of correction (e.g. 'curing', 'temperature')")
    factor: float = Field(..., description="Applied multiplier or shift factor")
    reason: str = Field(..., description="Explanation of why this correction was applied")


class DataFlags(BaseModel):
    """
    Quality flags indicating completeness, warnings, and error states.
    """
    missing_element_ref: bool = Field(False, description="True if element reference is missing")
    missing_temperature: bool = Field(False, description="True if concrete temperature is missing")
    no_resistivity_data: bool = Field(False, description="True if no resistivity readings are provided")
    insufficient_resistivity_readings: bool = Field(False, description="True if fewer than 8 resistivity readings are provided")
    insufficient_half_cell_readings: bool = Field(False, description="True if half-cell potential readings are provided but fewer than 3")
    high_resistivity_variance: bool = Field(False, description="True if coefficient of variation (COV) of resistivity readings exceeds 15%")


class SurfaceResistivityInput(BaseModel):
    """
    Input validation schema for surface resistivity and corrosion risk.
    """
    element_ref: str = Field(..., description="Structural element identifier")
    readings: List[float] = Field(default_factory=list, description="Raw surface resistivity readings in kΩ-cm")
    temperature: Optional[float] = Field(None, description="Concrete temperature at test time")
    temperature_unit: str = Field("C", description="Temperature unit: 'C' or 'F'")
    reference_temperature: float = Field(20.0, description="Reference temperature in °C (typically 20 or 25)")
    correction_method: str = Field("arrhenius", description="Correction model: 'arrhenius', 'linear', or 'none'")
    activation_energy: float = Field(DEFAULT_ACTIVATION_ENERGY, description="Arrhenius activation energy (J/mol)")
    linear_coefficient: float = Field(DEFAULT_LINEAR_COEFFICIENT, description="Linear temperature coefficient (percentage as decimal, e.g. 0.02)")
    curing_method: CuringMethod = Field(CuringMethod.moist_room, description="Curing method used for specimens")
    half_cell_readings: List[float] = Field(default_factory=list, description="Half-cell potential readings in mV")
    electrode_type: ElectrodeType = Field(ElectrodeType.CSE, description="Type of reference electrode used for half-cell")

    @field_validator("temperature_unit")
    @classmethod
    def validate_temp_unit(cls, v: str) -> str:
        clean = v.upper().strip()
        if clean not in ("C", "F"):
            raise ValueError("temperature_unit must be 'C' or 'F'")
        return clean

    @field_validator("correction_method")
    @classmethod
    def validate_correction_method(cls, v: str) -> str:
        clean = v.lower().strip()
        if clean not in ("arrhenius", "linear", "none"):
            raise ValueError("correction_method must be 'arrhenius', 'linear', or 'none'")
        return clean

    @field_validator("readings")
    @classmethod
    def validate_readings(cls, v: List[float]) -> List[float]:
        for idx, val in enumerate(v):
            if val <= 0:
                raise ValueError(f"Resistivity reading at index {idx} ({val} kΩ-cm) must be positive.")
        return v


class SurfaceResistivityContext(BaseModel):
    """
    Validated output context object representing surface resistivity and corrosion risk state.
    """
    element_ref: str = Field(..., description="Structural element identifier")
    measured_average: Optional[float] = Field(None, description="Raw average resistivity in kΩ-cm")
    corrected_resistivity: Optional[float] = Field(None, description="Resistivity after temperature and curing corrections (kΩ-cm)")
    corrections_applied: List[CorrectionLogEntry] = Field(default_factory=list, description="History of applied corrections")
    chloride_risk: Optional[ChlorideRisk] = Field(None, description="Chloride ion penetrability/permeability classification")
    half_cell_average: Optional[float] = Field(None, description="Average half-cell potential in mV")
    corrosion_risk: Optional[CorrosionRisk] = Field(None, description="Corrosion probability class (ASTM C876)")
    confidence_ceiling: int = Field(100, description="Reliability score from 0 to 100")
    flags: DataFlags = Field(..., description="Data completeness and quality flags")
    has_errors: bool = Field(False, description="True if calculations are blocked by missing data")

    @field_validator("confidence_ceiling")
    @classmethod
    def validate_confidence(cls, v: int) -> int:
        if not (0 <= v <= 100):
            raise ValueError("confidence_ceiling must be between 0 and 100")
        return v


# =====================================================================
# CALCULATION FUNCTIONS
# =====================================================================

def calculate_average(values: List[float]) -> Optional[float]:
    """Helper to calculate mean of float array."""
    if not values:
        return None
    return sum(values) / len(values)


def calculate_cov(values: List[float], mean: float) -> float:
    """Helper to calculate Coefficient of Variation (COV) as a ratio (SD / mean)."""
    if len(values) <= 1 or mean == 0:
        return 0.0
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    std_dev = math.sqrt(variance)
    return std_dev / mean


def convert_to_celsius(temp: float, unit: str) -> float:
    """Helper to convert Fahrenheit to Celsius."""
    if unit == "F":
        return (temp - 32.0) * 5.0 / 9.0
    return temp


def apply_corrections(
    raw_avg: float,
    temp_c: Optional[float],
    input_data: SurfaceResistivityInput
) -> tuple[float, List[CorrectionLogEntry]]:
    """
    Applies curing correction followed by temperature correction.
    Returns the corrected resistivity and a list of applied corrections.
    """
    logs = []
    current_val = raw_avg

    # 1. Curing Correction
    curing_factor = CURING_FACTORS[input_data.curing_method]
    if curing_factor != 1.0:
        current_val *= curing_factor
        logs.append(CorrectionLogEntry(
            type="curing",
            factor=curing_factor,
            reason=f"Specimen cured in lime water (AASHTO T 358 adjustment)"
        ))

    # 2. Temperature Correction
    if input_data.correction_method == "none" or temp_c is None:
        return round(current_val, 2), logs

    ref_temp = input_data.reference_temperature

    if input_data.correction_method == "arrhenius":
        # Convert Celsius to Kelvin
        t_kelvin = temp_c + 273.15
        t_ref_kelvin = ref_temp + 273.15
        
        # Arrhenius multiplier: exp( (E_a / R) * ( (1 / T_ref) - (1 / T) ) )
        exponent = (input_data.activation_energy / R_GAS_CONSTANT) * ((1.0 / t_ref_kelvin) - (1.0 / t_kelvin))
        temp_factor = math.exp(exponent)
        current_val *= temp_factor
        
        logs.append(CorrectionLogEntry(
            type="temperature_arrhenius",
            factor=round(temp_factor, 4),
            reason=f"Arrhenius correction from {round(temp_c, 1)}°C to {ref_temp}°C (E_a={input_data.activation_energy} J/mol)"
        ))

    elif input_data.correction_method == "linear":
        # Linear correction: 1 + alpha * (T - T_ref)
        temp_factor = 1.0 + input_data.linear_coefficient * (temp_c - ref_temp)
        # Prevent division by zero or negative values in extreme inputs
        if temp_factor < 0.1:
            temp_factor = 0.1
        current_val *= temp_factor
        
        logs.append(CorrectionLogEntry(
            type="temperature_linear",
            factor=round(temp_factor, 4),
            reason=f"Linear correction from {round(temp_c, 1)}°C to {ref_temp}°C (alpha={input_data.linear_coefficient}/°C)"
        ))

    return round(current_val, 2), logs


def classify_chloride_risk(resistivity: float) -> ChlorideRisk:
    """
    Maps corrected resistivity (kΩ-cm) to chloride ion penetrability / risk (AASHTO T 358).
    """
    if resistivity < 10.0:
        return ChlorideRisk.very_high
    elif resistivity < 20.0:
        return ChlorideRisk.high
    elif resistivity < 37.0:
        return ChlorideRisk.moderate
    elif resistivity < 254.0:
        return ChlorideRisk.low
    else:
        return ChlorideRisk.very_low


def classify_corrosion_risk(potential_mv: float, electrode: ElectrodeType) -> CorrosionRisk:
    """
    Maps half-cell potential measurement (mV) to corrosion risk band based on ASTM C876.
    Adjusts boundaries depending on the electrode type.
    """
    if electrode == ElectrodeType.CSE:
        # Copper-Copper Sulfate Electrode
        if potential_mv > -200.0:
            return CorrosionRisk.low
        elif potential_mv >= -350.0:
            return CorrosionRisk.uncertain
        else:
            return CorrosionRisk.high
            
    elif electrode == ElectrodeType.Calomel:
        # Saturated Calomel Electrode
        if potential_mv > -120.0:
            return CorrosionRisk.low
        elif potential_mv >= -270.0:
            return CorrosionRisk.uncertain
        else:
            return CorrosionRisk.high
            
    elif electrode == ElectrodeType.AgCl:
        # Silver-Silver Chloride Electrode
        if potential_mv > -100.0:
            return CorrosionRisk.low
        elif potential_mv >= -250.0:
            return CorrosionRisk.uncertain
        else:
            return CorrosionRisk.high

    # Default fallback
    return CorrosionRisk.uncertain


def compute_confidence_ceiling(
    input_data: SurfaceResistivityInput,
    cov: float,
    temp_c: Optional[float],
    corrosion_risk: Optional[CorrosionRisk]
) -> int:
    """
    Calculates reliability percentage based on data completeness and variability.
    """
    score = 100

    # 1. Deduct if resistivity sample size is small (< 8 readings)
    if len(input_data.readings) < 8:
        score -= 20

    # 2. Deduct if coefficient of variation is high (> 10%)
    if cov > 0.10:
        score -= 15

    # 3. Deduct if temperature correction is extreme (measured temp is outside 15°C - 25°C)
    if temp_c is not None and (temp_c < 15.0 or temp_c > 25.0) and input_data.correction_method != "none":
        score -= 15

    # 4. Deduct if half-cell measurements are few (< 3 readings)
    if input_data.half_cell_readings and len(input_data.half_cell_readings) < 3:
        score -= 20

    # 5. Deduct if corrosion activity probability is in the "uncertain" range
    if corrosion_risk == CorrosionRisk.uncertain:
        score -= 15

    # Clamp between 0 and 100
    return max(0, min(score, 100))


# =====================================================================
# MAIN PIPELINE ENTRYPOINT
# =====================================================================

def run_resistivity_engine(raw_input: Dict) -> SurfaceResistivityContext:
    """
    Ingests raw inputs, runs calculations, evaluates data quality,
    applies corrections, and produces a validated output context.
    """
    # 1. Parse and validate inputs
    inp = SurfaceResistivityInput(**raw_input)
    
    # 2. Check completeness flags
    flags = DataFlags(
        missing_element_ref=not inp.element_ref.strip(),
        missing_temperature=(inp.temperature is None),
        no_resistivity_data=(not inp.readings),
        insufficient_resistivity_readings=(len(inp.readings) > 0 and len(inp.readings) < 8),
        insufficient_half_cell_readings=(len(inp.half_cell_readings) > 0 and len(inp.half_cell_readings) < 3),
        high_resistivity_variance=False
    )

    # Calculate resistivity metrics if readings exist
    measured_avg = calculate_average(inp.readings)
    cov = 0.0
    if measured_avg is not None:
        cov = calculate_cov(inp.readings, measured_avg)
        flags.high_resistivity_variance = (cov > 0.15)

    # 3. Assess if we have enough core data to calculate classes
    # Temperature and resistivity average are critical. Without them, we block calculations.
    has_errors = flags.no_resistivity_data or flags.missing_temperature

    if has_errors:
        return SurfaceResistivityContext(
            element_ref=inp.element_ref,
            measured_average=measured_avg,
            corrected_resistivity=None,
            corrections_applied=[],
            chloride_risk=None,
            half_cell_average=calculate_average(inp.half_cell_readings),
            corrosion_risk=None,
            confidence_ceiling=0,
            flags=flags,
            has_errors=True
        )

    # 4. Perform calculations
    temp_c = convert_to_celsius(inp.temperature, inp.temperature_unit) if inp.temperature is not None else None
    
    # Apply curing and temperature corrections
    corrected_val, corrections = apply_corrections(measured_avg, temp_c, inp)
    
    # Classify chloride penetrability risk
    chloride_risk = classify_chloride_risk(corrected_val)

    # Process half-cell potential
    half_cell_avg = calculate_average(inp.half_cell_readings)
    corrosion_risk = None
    if half_cell_avg is not None:
        corrosion_risk = classify_corrosion_risk(half_cell_avg, inp.electrode_type)

    # Calculate confidence score
    confidence = compute_confidence_ceiling(inp, cov, temp_c, corrosion_risk)

    return SurfaceResistivityContext(
        element_ref=inp.element_ref,
        measured_average=round(measured_avg, 2) if measured_avg is not None else None,
        corrected_resistivity=corrected_val,
        corrections_applied=corrections,
        chloride_risk=chloride_risk,
        half_cell_average=round(half_cell_avg, 1) if half_cell_avg is not None else None,
        corrosion_risk=corrosion_risk,
        confidence_ceiling=confidence,
        flags=flags,
        has_errors=False
    )

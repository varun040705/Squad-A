"""
OX1 NDT Platform - UPV Module
Squad A - Complete Context Engine

Segments:
    A-1 : Moisture & Transmission Mode Correction
    A-2 : Aggregate Threshold Bands & Age Maturity Index
    A-3 : Element Reliability Ceiling & Final Context Object Assembly

Entry point:
    run_context_engine(raw_input) -> FinalContextObject

Author : Squad A
Standard: IS 13311
"""

from typing import Dict, List, Optional, Tuple
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, field_validator


# =====================================================================
# ENUMS
# =====================================================================

class AggregateType(str, Enum):
    """Aggregate type used in the UPV test."""
    standard    = "standard"
    lightweight = "lightweight"


class ElementType(str, Enum):
    """Structural element type the sensor was placed on."""
    column     = "column"
    beam       = "beam"
    wall       = "wall"
    slab       = "slab"
    foundation = "foundation"


# =====================================================================
# CONSTANTS
# =====================================================================

# --- A-1 Constants ---
MOISTURE_FACTORS = {
    "dry":           0.00,
    "slightly_damp": -0.04,
    "damp":          -0.09,
    "wet":           -0.18,
    "saturated":     -0.25,
}

MODE_PENALTIES = {
    "direct":      0.00,
    "semi_direct": -0.07,
    "indirect":    -0.13,
}

CONFIDENCE_CEILING_DEFAULT  = 100
CONFIDENCE_CEILING_INDIRECT = 60

# --- A-2 Constants ---
DENSE_BANDS = {
    "excellent": 4.5,   # > 4.5 km/s
    "good":      3.5,   # 3.5 – 4.5 km/s
    "medium":    3.0,   # 3.0 – 3.5 km/s
    "poor":      2.9,   # < 3.0 km/s  (corrected from original 3.0 — poor must be below medium)
}

LIGHTWEIGHT_BANDS = {
    "excellent": 3.2,
    "good":      2.5,
    "medium":    2.0,
    "poor":      1.8,
}

AGE_MATURITY = {
    3:  0.58,
    7:  0.74,
    14: 0.88,
    28: 1.00,
    90: 1.12,
}

AMI_THRESHOLD = 0.85

# --- A-3 Constants ---
ELEMENT_CONFIDENCE_CEILING = {
    "column":     95,
    "beam":       80,
    "wall":       75,
    "slab":       55,
    "foundation": 35,
}


# =====================================================================
# SHARED SCHEMA
# =====================================================================

class CorrectionLogEntry(BaseModel):
    type:   str   = Field(...)
    factor: float = Field(...)
    reason: str   = Field(...)


# =====================================================================
# A-1 : MOISTURE & MODE CORRECTION
# =====================================================================

class RawInput(BaseModel):
    """
    Master input schema for the entire Context Engine.
    All fields needed by A-1, A-2, and A-3 together.
    """
    element_id:         UUID          = Field(...)
    raw_velocity_kmps:  float         = Field(...)
    moisture_condition: str           = Field(...)
    transmission_mode:  str           = Field(...)
    aggregate_type:     AggregateType = Field(...)
    concrete_age_days:  int           = Field(...)
    v_28day_reference:  float         = Field(...)
    element_type:       ElementType   = Field(...)

    @field_validator("moisture_condition")
    @classmethod
    def validate_moisture(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in MOISTURE_FACTORS:
            raise ValueError(f"Unknown moisture condition '{v}'. Must be one of: {list(MOISTURE_FACTORS.keys())}")
        return v

    @field_validator("transmission_mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in MODE_PENALTIES:
            raise ValueError(f"Unknown transmission mode '{v}'. Must be one of: {list(MODE_PENALTIES.keys())}")
        return v

    @field_validator("raw_velocity_kmps", "v_28day_reference")
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Velocity must be positive.")
        return v

    @field_validator("concrete_age_days")
    @classmethod
    def must_be_positive_int(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("concrete_age_days must be positive.")
        return v


def _apply_moisture_correction(
    raw_velocity: float,
    moisture_condition: str
) -> Tuple[float, Optional[CorrectionLogEntry]]:
    factor    = MOISTURE_FACTORS[moisture_condition]
    corrected = round(raw_velocity * (1.0 + factor), 4)
    log       = None
    if factor != 0.0:
        log = CorrectionLogEntry(
            type="moisture",
            factor=factor,
            reason=f"{moisture_condition} condition"
        )
    return corrected, log


def _run_a1(inp: RawInput) -> Tuple[float, List[CorrectionLogEntry], int]:
    """
    A-1: Apply moisture correction first, then mode penalty.
    Returns (corrected_velocity, corrections_list, mode_ceiling).
    """
    corrections: List[CorrectionLogEntry] = []

    # Step 1 — Moisture
    after_moisture, moisture_log = _apply_moisture_correction(
        inp.raw_velocity_kmps, inp.moisture_condition
    )
    if moisture_log:
        corrections.append(moisture_log)

    # Step 2 — Mode penalty
    mode_penalty  = MODE_PENALTIES[inp.transmission_mode]
    final_velocity = after_moisture
    if mode_penalty != 0.0:
        final_velocity = round(after_moisture * (1.0 + mode_penalty), 4)
        corrections.append(CorrectionLogEntry(
            type="mode",
            factor=mode_penalty,
            reason=f"{inp.transmission_mode.replace('_', '-')} transmission"
        ))

    # Step 3 — Mode ceiling
    mode_ceiling = CONFIDENCE_CEILING_INDIRECT if inp.transmission_mode == "indirect" \
                   else CONFIDENCE_CEILING_DEFAULT

    return final_velocity, corrections, mode_ceiling


# =====================================================================
# A-2 : AGGREGATE BANDS & AGE MATURITY INDEX
# =====================================================================

def _get_effective_bands(aggregate_type: AggregateType) -> Dict[str, float]:
    """A-2: Return quality threshold bands for the given aggregate type."""
    if aggregate_type == AggregateType.lightweight:
        return LIGHTWEIGHT_BANDS
    return DENSE_BANDS


def _compute_ami(
    v_actual: float,
    age_days: int,
    v_28day_reference: float
) -> Tuple[Optional[float], bool]:
    """
    A-2: Compute Age Maturity Index.
    AMI = V_actual / V_expected_for_age
    V_expected = v_28day_reference * maturity_factor

    Returns (ami, underperformance_flag).
    - ami is None if age_days is not in the maturity table.
    - underperformance_flag is True only when AMI is computed and < 0.85.
      If age is unsupported, underperformance is False — it is flagged
      separately as "unavailable" in _build_flags, not as underperformance.
    """
    factor = AGE_MATURITY.get(age_days)
    if factor is None:
        return None, False  # age unsupported → ami unavailable, not underperformance

    v_expected = v_28day_reference * factor
    ami        = round(v_actual / v_expected, 3)
    return ami, ami < AMI_THRESHOLD


def _run_a2(
    inp: RawInput,
    corrected_velocity: float
) -> Tuple[Dict[str, float], Optional[float], bool, List[CorrectionLogEntry]]:
    """
    A-2: Returns (effective_bands, ami, age_underperformance, corrections).
    """
    corrections: List[CorrectionLogEntry] = []

    effective_bands = _get_effective_bands(inp.aggregate_type)

    ami, underperformance = _compute_ami(
        v_actual=corrected_velocity,
        age_days=inp.concrete_age_days,
        v_28day_reference=inp.v_28day_reference
    )

    if ami is None:
        corrections.append(CorrectionLogEntry(
            type="age_maturity",
            factor=0.0,
            reason=f"unsupported age {inp.concrete_age_days} days"
        ))

    return effective_bands, ami, underperformance, corrections


# =====================================================================
# A-3 : ELEMENT RELIABILITY CEILING & ASSEMBLY
# =====================================================================

class FinalContextObject(BaseModel):
    """
    The validated final context object released to downstream squads (B, C, D, E).

    Field notes:
    - corrected_velocity_kmps : renamed from A-1's moisture_corrected_velocity
                                (moisture + mode corrections both applied)
    - flags                   : merged from A-1 (indirect mode) and A-2 (AMI)
    """
    element_id:              UUID
    element_type:            ElementType
    raw_velocity_kmps:       float                    # original reading, no corrections
    corrected_velocity_kmps: float                    # after moisture + mode corrections (from A-1)
    corrections_applied:     List[CorrectionLogEntry] # merged A-1 + A-2 correction logs
    effective_bands:         Dict[str, float]          # from A-2 (aggregate-aware)
    age_mismatch_index:      Optional[float]           # AMI from A-2, None if age unsupported
    confidence_ceiling:      int                       # most restrictive of element + mode ceilings
    flags:                   List[str]                 # merged A-1 + A-2 flags

    @field_validator("raw_velocity_kmps", "corrected_velocity_kmps")
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Velocity must be positive.")
        return v

    @field_validator("confidence_ceiling")
    @classmethod
    def ceiling_must_be_valid(cls, v: int) -> int:
        if not (0 <= v <= 100):
            raise ValueError("confidence_ceiling must be between 0 and 100.")
        return v

    @field_validator("effective_bands")
    @classmethod
    def bands_must_not_be_empty(cls, v: Dict) -> Dict:
        if not v:
            raise ValueError("effective_bands cannot be empty.")
        return v


def _resolve_ceiling(element_type: ElementType, mode_ceiling: int) -> int:
    """
    A-3: Return the most restrictive (lowest) ceiling between
    element type ceiling and indirect mode ceiling.
    """
    element_ceiling = ELEMENT_CONFIDENCE_CEILING[element_type.value]
    return min(element_ceiling, mode_ceiling)


def _build_flags(
    transmission_mode: str,
    age_underperformance: bool,
    ami: Optional[float]
) -> List[str]:
    """A-3: Build the flags list from A-1 and A-2 results."""
    flags: List[str] = []

    if transmission_mode == "indirect":
        flags.append("indirect mode applied — confidence capped at 60")

    if age_underperformance and ami is not None:
        flags.append(f"age underperformance: AMI {ami} is below threshold {AMI_THRESHOLD}")

    if ami is None:
        flags.append("age maturity index unavailable: unsupported concrete age")

    return flags


# =====================================================================
# MAIN ENTRY POINT
# =====================================================================

def run_context_engine(raw_input: Dict) -> FinalContextObject:
    """
    Full Squad A Context Engine pipeline.

    Takes a single raw input dict and returns a validated FinalContextObject
    ready for downstream squads.

    Pipeline:
        raw_input → A-1 (moisture + mode) → A-2 (bands + AMI) → A-3 (ceiling + assembly)

    Args:
        raw_input: dict with keys:
            element_id, raw_velocity_kmps, moisture_condition,
            transmission_mode, aggregate_type, concrete_age_days,
            v_28day_reference, element_type

    Returns:
        FinalContextObject (Pydantic validated)

    Raises:
        ValidationError — if any field is missing or invalid
    """

    # --- Validate master input ---
    inp = RawInput(**raw_input)

    # --- A-1: Moisture + Mode Correction ---
    corrected_velocity, a1_corrections, mode_ceiling = _run_a1(inp)

    # --- A-2: Aggregate Bands + AMI ---
    effective_bands, ami, age_underperformance, a2_corrections = _run_a2(
        inp, corrected_velocity
    )

    # --- A-3: Ceiling + Assembly ---
    confidence_ceiling  = _resolve_ceiling(inp.element_type, mode_ceiling)
    all_corrections     = a1_corrections + a2_corrections
    flags               = _build_flags(inp.transmission_mode, age_underperformance, ami)

    return FinalContextObject(
        element_id=inp.element_id,
        element_type=inp.element_type,
        raw_velocity_kmps=inp.raw_velocity_kmps,
        corrected_velocity_kmps=corrected_velocity,
        corrections_applied=all_corrections,
        effective_bands=effective_bands,
        age_mismatch_index=ami,
        confidence_ceiling=confidence_ceiling,
        flags=flags
    )


# =====================================================================
# ACCEPTANCE TESTS
# =====================================================================

if __name__ == "__main__":

    from uuid import uuid4
    import json

    def print_result(label: str, result: FinalContextObject):
        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"{'='*60}")
        print(json.dumps(result.model_dump(mode="json"), indent=2))

    test_id = uuid4()

    # ------------------------------------------------------------------
    # Test 1: Wet + Direct + Standard + Foundation
    # Expected: corrected ~3.69 km/s, ceiling=35, no AMI flag
    # ------------------------------------------------------------------
    r1 = run_context_engine({
        "element_id":        test_id,
        "raw_velocity_kmps": 4.5,
        "moisture_condition":"wet",
        "transmission_mode": "direct",
        "aggregate_type":    "standard",
        "concrete_age_days": 28,
        "v_28day_reference": 4.0,
        "element_type":      "foundation"
    })
    assert r1.confidence_ceiling == 35,        f"FAILED T1 ceiling: {r1.confidence_ceiling}"
    assert r1.corrected_velocity_kmps == 3.69, f"FAILED T1 velocity: {r1.corrected_velocity_kmps}"
    print_result("TEST 1: Foundation + Wet + Direct → ceiling=35, velocity=3.69", r1)

    # ------------------------------------------------------------------
    # Test 2: Column + Indirect mode → ceiling = min(95, 60) = 60
    # ------------------------------------------------------------------
    r2 = run_context_engine({
        "element_id":        test_id,
        "raw_velocity_kmps": 4.5,
        "moisture_condition":"dry",
        "transmission_mode": "indirect",
        "aggregate_type":    "standard",
        "concrete_age_days": 28,
        "v_28day_reference": 4.0,
        "element_type":      "column"
    })
    assert r2.confidence_ceiling == 60, f"FAILED T2 ceiling: {r2.confidence_ceiling}"
    print_result("TEST 2: Column + Indirect → ceiling=60", r2)

    # ------------------------------------------------------------------
    # Test 3: Slab + Indirect → ceiling = min(55, 60) = 55
    # ------------------------------------------------------------------
    r3 = run_context_engine({
        "element_id":        test_id,
        "raw_velocity_kmps": 4.0,
        "moisture_condition":"dry",
        "transmission_mode": "indirect",
        "aggregate_type":    "standard",
        "concrete_age_days": 28,
        "v_28day_reference": 4.0,
        "element_type":      "slab"
    })
    assert r3.confidence_ceiling == 55, f"FAILED T3 ceiling: {r3.confidence_ceiling}"
    print_result("TEST 3: Slab + Indirect → ceiling=55", r3)

    # ------------------------------------------------------------------
    # Test 4: Lightweight aggregate → lightweight bands must be used
    # ------------------------------------------------------------------
    r4 = run_context_engine({
        "element_id":        test_id,
        "raw_velocity_kmps": 2.8,
        "moisture_condition":"dry",
        "transmission_mode": "direct",
        "aggregate_type":    "lightweight",
        "concrete_age_days": 28,
        "v_28day_reference": 3.0,
        "element_type":      "beam"
    })
    assert r4.effective_bands["good"] == 2.5, f"FAILED T4 bands: {r4.effective_bands}"
    print_result("TEST 4: Lightweight aggregate → lightweight bands", r4)

    # ------------------------------------------------------------------
    # Test 5: AMI < 0.85 → age underperformance flag
    # ------------------------------------------------------------------
    r5 = run_context_engine({
        "element_id":        test_id,
        "raw_velocity_kmps": 3.0,
        "moisture_condition":"dry",
        "transmission_mode": "direct",
        "aggregate_type":    "standard",
        "concrete_age_days": 7,
        "v_28day_reference": 4.5,
        "element_type":      "wall"
    })
    assert any("age underperformance" in f for f in r5.flags), f"FAILED T5 flags: {r5.flags}"
    print_result("TEST 5: AMI < 0.85 → age underperformance flag", r5)

    # ------------------------------------------------------------------
    # Test 6: Bad input → Pydantic rejects it
    # ------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("  TEST 6: Malformed input → must be rejected")
    print(f"{'='*60}")
    try:
        run_context_engine({"element_id": test_id})
        print("  FAILED: should have raised ValidationError")
    except Exception as e:
        print(f"  Correctly rejected ✅  ({type(e).__name__})")

    # ------------------------------------------------------------------
    # Velocity sanity check: L=300mm, T=75µs must give exactly 4.0000 km/s
    # ------------------------------------------------------------------
    L_mm = 300
    T_us = 75
    v_check = (L_mm / 1000) / (T_us / 1_000_000) / 1000
    assert v_check == 4.0, f"FAILED velocity formula: {v_check}"
    print(f"\n{'='*60}")
    print(f"  VELOCITY SANITY CHECK: L=300, T=75 → {v_check} km/s ✅")
    print(f"{'='*60}")

    print("\n✅ All tests passed — Squad A Context Engine is ready.\n")

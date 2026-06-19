# Segment A-1: Moisture & Mode Correction Module

Part of the **OX1 UPV Context Engine**. This module ingests a raw ultrasonic pulse velocity (UPV) reading along with concrete moisture and transmission-mode metadata, applies the appropriate corrections, logs each adjustment, and enforces a confidence ceiling on the resulting reading.

## Overview

Raw UPV readings are distorted by how wet the concrete is and by how the pulse transducers are arranged (direct, semi-direct, or indirect transmission). This module corrects for both effects in a deterministic, auditable way and produces a validated `UPVReadingContext` object that downstream segments (starting with SA-2) consume.

## Files

| File | Purpose |
|---|---|
| `context.py` | Core correction logic and Pydantic v2 schemas |
| `test_context.py` | Pytest suite covering corrections, ceilings, and validation errors |
| `seed_data.json` | Synthetic concrete element records for local testing |
| `ox1.db` | Empty SQLite placeholder for future persistence |

## Correction Logic

Corrections are applied in order: **moisture first, then transmission mode.**

### Moisture Factors

| Condition | Factor |
|---|---|
| `dry` | 0% (0.00) |
| `slightly_damp` | -4% (-0.04) |
| `damp` | -9% (-0.09) |
| `wet` | -18% (-0.18) |
| `saturated` | -25% (-0.25) |

### Transmission Mode Penalties

| Mode | Penalty |
|---|---|
| `direct` | 0% (0.00) |
| `semi_direct` | -7% (-0.07) |
| `indirect` | -13% (-0.13) |

### Confidence Ceiling

- Default ceiling: **100**
- If transmission mode is `indirect`, the ceiling is capped at **60**, regardless of how clean the corrected reading looks.

### Correction Logging

Every non-zero correction is appended to `corrections_applied[]` in the chronological order it was applied (moisture, then mode), recording the correction type, factor, and reason.

## Validation

Both input and output are strictly validated using **Pydantic v2**:

- `UPVInputReading` — validates the raw input (positive velocity, valid element ID, recognized moisture condition and transmission mode).
- `UPVReadingContext` — validates the final, frozen output context before it's handed downstream.

Invalid moisture conditions, invalid transmission modes, and non-positive velocities all raise validation errors rather than silently passing through.

## Example

```json
{
  "element_id": "a1b2-c3d4-...",
  "raw_velocity_kmps": 4.5000,
  "moisture_corrected_velocity": 3.6900,
  "corrections_applied": [
    {"type": "moisture", "factor": -0.18, "reason": "wet condition"}
  ],
  "confidence_ceiling": 100
}
```

A `wet` reading at `4.5 km/s` is corrected by -18% to `3.6900 km/s`. If the transmission mode were also `indirect`, the mode penalty (-13%) would apply on top of the moisture correction, yielding `3.2103 km/s`, and the confidence ceiling would drop to `60`.

## Testing

Run the suite with:

```bash
python -m pytest -v
```

Expected output:

```
tests/test_context.py::test_moisture_correction PASSED                   [ 12%]
tests/test_context.py::test_moisture_and_mode_corrections PASSED         [ 25%]
tests/test_context.py::test_pipeline_acceptance_test_1 PASSED            [ 37%]
tests/test_context.py::test_pipeline_acceptance_test_2 PASSED            [ 50%]
tests/test_context.py::test_pipeline_acceptance_test_3 PASSED            [ 62%]
tests/test_context.py::test_validation_invalid_moisture PASSED           [ 75%]
tests/test_context.py::test_validation_invalid_mode PASSED               [ 87%]
tests/test_context.py::test_validation_invalid_velocity PASSED           [100%]
============================== 8 passed in 0.13s ==============================
```

Coverage includes:

- Wet concrete at raw 4.5 km/s → corrects to 3.6900 km/s
- Dry concrete at raw 3.0 km/s → no corrections logged, stays at 3.0000 km/s
- Saturated concrete at raw 5.0 km/s → corrects to 3.7500 km/s
- Wet + indirect mode combine to 3.2103 km/s, confidence ceiling capped at 60
- Invalid moisture condition, invalid transmission mode, and negative velocity all raise validation errors

## Downstream Hand-off (→ SA-2)

The `UPVReadingContext` object produced here is handed to the **SA-2 engineer (Aggregate & Age Correction Specialist)**, who uses it as follows:

1. **Age Maturity Index (AMI)** — `moisture_corrected_velocity` becomes `V_actual` in `AMI = V_actual / V_expected_for_age`, where `V_expected_for_age` is derived from the concrete's age and grade.
2. **Age Flag** — if the computed AMI is below `0.85`, SA-2 appends a warning flag (e.g. "velocity below expected for age").
3. **Quality Bands** — SA-2 selects `effective_bands` based on aggregate type, so downstream teams know whether to grade against lightweight or standard thresholds.
4. **Pass-through** — `corrections_applied` and `confidence_ceiling` are carried forward unchanged to SA-3, who assembles the final context object for Squads B, C, D, and E.

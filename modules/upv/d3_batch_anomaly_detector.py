"""
OX1 NDT Platform - UPV Module
Squad D - Segment D-3: Batch Anomaly Detector & Combined Output

Groups per-element readings by pour date and concrete supplier. If
multiple elements poured together all show weakness, flags the whole
batch rather than treating each element as an isolated finding.

Flag condition
--------------
3 or more elements from the same pour date (and supplier) with mean
velocity below 3.5 km/s.

Hard rule
---------
Never flag a batch with fewer than 3 affected elements - an isolated
weak element is not a batch problem.

This module also assembles Segments D-1, D-2, and D-3 into the final
combined Squad D output.

Sensor Fusion Only
------------------
No Acoustic Emission. No Visual Inspection. No Electrical Surface
Resistivity.
"""

from __future__ import annotations

from statistics import mean
from typing import Dict, List, Tuple

from pydantic import BaseModel, Field, field_validator

from modules.upv.d1_contractor_performance_tracker import (
    ContractorAlert,
    ContractorReading,
    compute_contractor_alerts,
)
from modules.upv.d2_element_deterioration_tracker import (
    ElementDeteriorationFlag,
    ElementVisit,
    compute_deterioration_flags,
)


# =====================================================================
# CONSTANTS
# =====================================================================

MIN_AFFECTED_ELEMENTS_FOR_BATCH_FLAG = 3

BATCH_WEAKNESS_THRESHOLD_KMPS = 3.5

BATCH_ANOMALY_SEVERITY = "warning"


# =====================================================================
# SCHEMAS
# =====================================================================

class BatchReading(BaseModel):
    """
    One element's mean UPV reading for a single pour, read from the
    database. Each element contributes exactly one mean velocity per
    pour date/supplier combination.
    """

    element_ref: str = Field(..., min_length=1)
    pour_date: str = Field(..., min_length=1, description="ISO date string, e.g. '2026-06-01'.")
    supplier: str = Field(..., min_length=1)
    mean_velocity_kmps: float = Field(..., gt=0)

    @field_validator("element_ref", "pour_date", "supplier")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Value cannot be blank.")
        return v


class BatchAnomaly(BaseModel):
    """Flag emitted when 3+ elements from the same pour show weakness together."""

    pour_date: str = Field(...)
    supplier: str = Field(...)
    affected_element_refs: List[str] = Field(..., min_length=MIN_AFFECTED_ELEMENTS_FOR_BATCH_FLAG)
    affected_count: int = Field(..., ge=MIN_AFFECTED_ELEMENTS_FOR_BATCH_FLAG)
    mean_velocity_kmps: float = Field(..., gt=0)
    severity: str = Field(...)


class CombinedPatternOutput(BaseModel):
    """Final Squad D output: all three detectors assembled together."""

    contractor_alerts: List[ContractorAlert] = Field(default_factory=list)
    deteriorating_elements: List[ElementDeteriorationFlag] = Field(default_factory=list)
    batch_anomalies: List[BatchAnomaly] = Field(default_factory=list)


# =====================================================================
# INTERNAL HELPERS
# =====================================================================

def _group_by_pour(readings: List[BatchReading]) -> Dict[Tuple[str, str], List[BatchReading]]:
    grouped: Dict[Tuple[str, str], List[BatchReading]] = {}
    for reading in readings:
        key = (reading.pour_date, reading.supplier)
        grouped.setdefault(key, []).append(reading)
    return grouped


# =====================================================================
# PUBLIC ENTRY POINTS
# =====================================================================

def compute_batch_anomalies(readings: List[BatchReading]) -> List[BatchAnomaly]:
    """
    Compute batch anomaly flags across the given per-element pour
    readings.

    Hard rule: a pour/supplier group with fewer than
    MIN_AFFECTED_ELEMENTS_FOR_BATCH_FLAG weak elements is never
    flagged - an isolated weak element is not a batch problem.
    """
    grouped = _group_by_pour(readings)
    anomalies: List[BatchAnomaly] = []

    for (pour_date, supplier), pour_readings in grouped.items():
        affected = [
            reading
            for reading in pour_readings
            if reading.mean_velocity_kmps < BATCH_WEAKNESS_THRESHOLD_KMPS
        ]

        if len(affected) < MIN_AFFECTED_ELEMENTS_FOR_BATCH_FLAG:
            continue

        affected_velocities = [reading.mean_velocity_kmps for reading in affected]

        anomalies.append(
            BatchAnomaly(
                pour_date=pour_date,
                supplier=supplier,
                affected_element_refs=[reading.element_ref for reading in affected],
                affected_count=len(affected),
                mean_velocity_kmps=round(mean(affected_velocities), 3),
                severity=BATCH_ANOMALY_SEVERITY,
            )
        )

    return anomalies


def assemble_combined_pattern_output(
    contractor_readings: List[ContractorReading],
    element_visits: List[ElementVisit],
    batch_readings: List[BatchReading],
) -> CombinedPatternOutput:
    """
    Run all three Squad D detectors (D-1, D-2, D-3) and assemble their
    results into the final combined output object.
    """
    return CombinedPatternOutput(
        contractor_alerts=compute_contractor_alerts(contractor_readings),
        deteriorating_elements=compute_deterioration_flags(element_visits),
        batch_anomalies=compute_batch_anomalies(batch_readings),
    )


# =====================================================================
# PUBLIC EXPORTS
# =====================================================================

__all__ = [
    "BatchReading",
    "BatchAnomaly",
    "CombinedPatternOutput",
    "compute_batch_anomalies",
    "assemble_combined_pattern_output",
]

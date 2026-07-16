"""
tests/test_d3_batch_anomaly_detector.py

Unit tests for Segment D-3: batch anomaly detector & combined output.

No AI call here. compute_batch_anomalies is tested directly with
synthetic BatchReading data; assemble_combined_pattern_output is tested
as an integration point wiring D-1, D-2, and D-3 together.
"""

from __future__ import annotations

import pytest

from modules.upv.d1_contractor_performance_tracker import ContractorReading
from modules.upv.d2_element_deterioration_tracker import ElementVisit
from modules.upv.d3_batch_anomaly_detector import (
    BATCH_ANOMALY_SEVERITY,
    BatchAnomaly,
    BatchReading,
    CombinedPatternOutput,
    MIN_AFFECTED_ELEMENTS_FOR_BATCH_FLAG,
    assemble_combined_pattern_output,
    compute_batch_anomalies,
)


def _batch_reading(element_ref: str, pour_date: str, supplier: str, velocity: float) -> BatchReading:
    return BatchReading(
        element_ref=element_ref,
        pour_date=pour_date,
        supplier=supplier,
        mean_velocity_kmps=velocity,
    )


class TestBatchReadingModel:
    def test_valid_reading_constructs(self) -> None:
        reading = _batch_reading("C-01", "2026-06-01", "Acme Concrete", 3.2)
        assert reading.element_ref == "C-01"

    def test_rejects_non_positive_velocity(self) -> None:
        with pytest.raises(Exception):
            BatchReading(
                element_ref="C-01",
                pour_date="2026-06-01",
                supplier="Acme Concrete",
                mean_velocity_kmps=0,
            )

    def test_rejects_blank_supplier(self) -> None:
        with pytest.raises(Exception):
            BatchReading(
                element_ref="C-01",
                pour_date="2026-06-01",
                supplier="   ",
                mean_velocity_kmps=3.2,
            )


class TestComputeBatchAnomalies:
    def test_five_weak_elements_same_pour_flagged(self) -> None:
        """
        Acceptance case: batch of 5 elements poured same day with mean
        3.2 km/s -> batch anomaly flagged with all affected element
        refs listed.
        """
        readings = [
            _batch_reading(f"C-0{i}", "2026-06-01", "Acme Concrete", 3.2)
            for i in range(1, 6)
        ]

        anomalies = compute_batch_anomalies(readings)

        assert len(anomalies) == 1
        anomaly = anomalies[0]
        assert isinstance(anomaly, BatchAnomaly)
        assert anomaly.pour_date == "2026-06-01"
        assert anomaly.supplier == "Acme Concrete"
        assert set(anomaly.affected_element_refs) == {"C-01", "C-02", "C-03", "C-04", "C-05"}
        assert anomaly.affected_count == 5
        assert anomaly.mean_velocity_kmps == 3.2
        assert anomaly.severity == BATCH_ANOMALY_SEVERITY

    def test_isolated_weak_element_not_flagged(self) -> None:
        """An isolated weak element is not a batch problem."""
        readings = [
            _batch_reading("C-01", "2026-06-01", "Acme Concrete", 3.2),
            _batch_reading("C-02", "2026-06-01", "Acme Concrete", 4.0),
            _batch_reading("C-03", "2026-06-01", "Acme Concrete", 4.1),
        ]
        assert compute_batch_anomalies(readings) == []

    def test_exactly_two_weak_elements_not_flagged(self) -> None:
        """Hard rule: fewer than 3 affected elements never flags a batch."""
        readings = [
            _batch_reading("C-01", "2026-06-01", "Acme Concrete", 3.0),
            _batch_reading("C-02", "2026-06-01", "Acme Concrete", 3.1),
            _batch_reading("C-03", "2026-06-01", "Acme Concrete", 4.2),
        ]
        assert compute_batch_anomalies(readings) == []

    def test_exactly_three_weak_elements_flagged(self) -> None:
        readings = [
            _batch_reading("C-01", "2026-06-01", "Acme Concrete", 3.0),
            _batch_reading("C-02", "2026-06-01", "Acme Concrete", 3.1),
            _batch_reading("C-03", "2026-06-01", "Acme Concrete", 3.2),
            _batch_reading("C-04", "2026-06-01", "Acme Concrete", 4.5),
        ]
        anomalies = compute_batch_anomalies(readings)
        assert len(anomalies) == 1
        assert anomalies[0].affected_count == 3
        assert "C-04" not in anomalies[0].affected_element_refs

    def test_different_pour_dates_not_grouped_together(self) -> None:
        readings = [
            _batch_reading("C-01", "2026-06-01", "Acme Concrete", 3.0),
            _batch_reading("C-02", "2026-06-02", "Acme Concrete", 3.0),
            _batch_reading("C-03", "2026-06-03", "Acme Concrete", 3.0),
        ]
        assert compute_batch_anomalies(readings) == []

    def test_different_suppliers_same_day_not_grouped_together(self) -> None:
        readings = [
            _batch_reading("C-01", "2026-06-01", "Acme Concrete", 3.0),
            _batch_reading("C-02", "2026-06-01", "Beta Concrete", 3.0),
            _batch_reading("C-03", "2026-06-01", "Gamma Concrete", 3.0),
        ]
        assert compute_batch_anomalies(readings) == []

    def test_healthy_batch_not_flagged(self) -> None:
        readings = [
            _batch_reading(f"C-0{i}", "2026-06-01", "Acme Concrete", 4.0)
            for i in range(1, 6)
        ]
        assert compute_batch_anomalies(readings) == []

    def test_multiple_independent_batches_both_flagged(self) -> None:
        readings = [
            _batch_reading("C-01", "2026-06-01", "Acme Concrete", 3.0),
            _batch_reading("C-02", "2026-06-01", "Acme Concrete", 3.1),
            _batch_reading("C-03", "2026-06-01", "Acme Concrete", 3.2),
            _batch_reading("C-04", "2026-06-05", "Beta Concrete", 2.9),
            _batch_reading("C-05", "2026-06-05", "Beta Concrete", 3.0),
            _batch_reading("C-06", "2026-06-05", "Beta Concrete", 3.1),
        ]
        anomalies = compute_batch_anomalies(readings)
        assert len(anomalies) == 2
        suppliers = {a.supplier for a in anomalies}
        assert suppliers == {"Acme Concrete", "Beta Concrete"}


class TestAssembleCombinedPatternOutput:
    def test_combined_output_wires_all_three_detectors(self) -> None:
        # D-1: fewer than 20 readings -> no contractor alerts possible.
        contractor_readings = [
            ContractorReading(
                contractor_name="Ravi Civil Works",
                project_id="PRJ-1",
                week_number=1,
                corrected_velocity_kmps=4.0,
            )
        ]

        # D-2: declining element, 3 visits.
        element_visits = [
            ElementVisit(element_ref="C-07", visit_month=0, corrected_velocity_kmps=4.2),
            ElementVisit(element_ref="C-07", visit_month=1, corrected_velocity_kmps=4.0),
            ElementVisit(element_ref="C-07", visit_month=2, corrected_velocity_kmps=3.85),
        ]

        # D-3: 5-element weak batch.
        batch_readings = [
            _batch_reading(f"C-0{i}", "2026-06-01", "Acme Concrete", 3.2)
            for i in range(1, 6)
        ]

        result = assemble_combined_pattern_output(
            contractor_readings, element_visits, batch_readings
        )

        assert isinstance(result, CombinedPatternOutput)
        assert result.contractor_alerts == []  # hard rule: <20 total readings
        assert len(result.deteriorating_elements) == 1
        assert result.deteriorating_elements[0].element_ref == "C-07"
        assert len(result.batch_anomalies) == 1
        assert result.batch_anomalies[0].affected_count == 5

    def test_empty_inputs_produce_empty_combined_output(self) -> None:
        result = assemble_combined_pattern_output([], [], [])

        assert result.contractor_alerts == []
        assert result.deteriorating_elements == []
        assert result.batch_anomalies == []


class TestBatchAnomalySchema:
    def test_rejects_affected_element_refs_below_minimum(self) -> None:
        with pytest.raises(Exception):
            BatchAnomaly(
                pour_date="2026-06-01",
                supplier="Acme Concrete",
                affected_element_refs=["C-01", "C-02"],
                affected_count=2,
                mean_velocity_kmps=3.0,
                severity="warning",
            )

    def test_min_affected_elements_constant_is_three(self) -> None:
        assert MIN_AFFECTED_ELEMENTS_FOR_BATCH_FLAG == 3
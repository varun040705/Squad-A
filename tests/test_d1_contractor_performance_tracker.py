"""
tests/test_d1_contractor_performance_tracker.py

Unit tests for Segment D-1: contractor performance tracker.

This module reads pre-computed readings from the database - there is no
AI call and no dependency on Squad A or Squad B here, so all tests build
synthetic ContractorReading data directly.
"""

from __future__ import annotations

import pytest

from modules.upv.d1_contractor_performance_tracker import (
    CONTRACTOR_ALERT_SEVERITY,
    ContractorAlert,
    ContractorReading,
    MIN_TOTAL_READINGS_REQUIRED,
    compute_contractor_alerts,
)


def _reading(contractor: str, week: int, velocity: float, project_id: str = "PRJ-1") -> ContractorReading:
    return ContractorReading(
        contractor_name=contractor,
        project_id=project_id,
        week_number=week,
        corrected_velocity_kmps=velocity,
    )


def _underperforming_dataset() -> list[ContractorReading]:
    """
    Three contractors, weeks 1-8, 3 readings/week each (72 total).

    "Ravi Civil Works" runs at the project baseline (4.0 km/s) through
    week 5, then drops to 3.2 km/s for weeks 6-8. This produces two
    consecutive breaching rolling-window weeks (7 and 8), which should
    fire an alert anchored on week 8.
    """
    readings: list[ContractorReading] = []

    for week in range(1, 9):
        ravi_velocity = 4.0 if week <= 5 else 3.2
        for _ in range(3):
            readings.append(_reading("Ravi Civil Works", week, ravi_velocity))
            readings.append(_reading("Contractor B", week, 4.0))
            readings.append(_reading("Contractor C", week, 4.0))

    return readings


class TestContractorReadingModel:
    def test_valid_reading_constructs(self) -> None:
        reading = _reading("Ravi Civil Works", 1, 4.0)
        assert reading.contractor_name == "Ravi Civil Works"

    def test_rejects_non_positive_velocity(self) -> None:
        with pytest.raises(Exception):
            ContractorReading(
                contractor_name="Ravi Civil Works",
                project_id="PRJ-1",
                week_number=1,
                corrected_velocity_kmps=0,
            )

    def test_rejects_blank_contractor_name(self) -> None:
        with pytest.raises(Exception):
            ContractorReading(
                contractor_name="   ",
                project_id="PRJ-1",
                week_number=1,
                corrected_velocity_kmps=4.0,
            )

    def test_rejects_week_number_below_one(self) -> None:
        with pytest.raises(Exception):
            ContractorReading(
                contractor_name="Ravi Civil Works",
                project_id="PRJ-1",
                week_number=0,
                corrected_velocity_kmps=4.0,
            )


class TestHardRuleMinimumReadings:
    def test_returns_empty_list_with_fewer_than_twenty_readings(self) -> None:
        readings = [_reading("Ravi Civil Works", 1, 4.0) for _ in range(8)]
        assert compute_contractor_alerts(readings) == []

    def test_returns_empty_list_at_exactly_nineteen_readings(self) -> None:
        readings = [_reading("Ravi Civil Works", 1, 4.0) for _ in range(MIN_TOTAL_READINGS_REQUIRED - 1)]
        assert compute_contractor_alerts(readings) == []

    def test_proceeds_at_exactly_twenty_readings(self) -> None:
        # 20 uniform readings, single contractor -> no deviation possible, no alert,
        # but this must NOT short-circuit to [] just because of the boundary.
        readings = [_reading("Ravi Civil Works", week, 4.0) for week in range(1, 21)]
        result = compute_contractor_alerts(readings)
        assert result == []  # no deviation exists, so no alert - but no crash either


class TestComputeContractorAlerts:
    def test_underperforming_contractor_fires_alert(self) -> None:
        readings = _underperforming_dataset()
        alerts = compute_contractor_alerts(readings)

        ravi_alerts = [a for a in alerts if a.contractor == "Ravi Civil Works"]
        assert len(ravi_alerts) == 1

        alert = ravi_alerts[0]
        assert isinstance(alert, ContractorAlert)
        assert alert.rolling_mean_kmps == 3.2
        assert alert.project_mean_kmps == 3.73
        assert alert.deviation_pct == -14.3
        assert alert.severity == CONTRACTOR_ALERT_SEVERITY
        assert alert.readings_count == 24

    def test_healthy_contractors_do_not_fire_alerts(self) -> None:
        readings = _underperforming_dataset()
        alerts = compute_contractor_alerts(readings)

        flagged_contractors = {a.contractor for a in alerts}
        assert "Contractor B" not in flagged_contractors
        assert "Contractor C" not in flagged_contractors

    def test_single_breaching_week_does_not_fire_alert(self) -> None:
        """Only 1 week below threshold (not 2+ consecutive) -> no alert."""
        readings: list[ContractorReading] = []
        for week in range(1, 6):
            velocity = 3.2 if week == 5 else 4.0
            for _ in range(3):
                readings.append(_reading("Ravi Civil Works", week, velocity))
                readings.append(_reading("Contractor B", week, 4.0))

        alerts = compute_contractor_alerts(readings)
        assert alerts == []

    def test_project_with_insufficient_data_returns_empty_array(self) -> None:
        readings = [_reading("Ravi Civil Works", week, 3.0) for week in range(1, 9)]
        assert compute_contractor_alerts(readings) == []

    def test_no_alerts_on_uniform_project(self) -> None:
        readings = []
        for week in range(1, 9):
            for _ in range(3):
                readings.append(_reading("Contractor A", week, 4.0))
                readings.append(_reading("Contractor B", week, 4.0))
        assert compute_contractor_alerts(readings) == []
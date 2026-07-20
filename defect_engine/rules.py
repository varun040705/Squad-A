"""
rules.py

Rule-based Defect Detection Engine.

Author: Sai Varun
Project: OX1 - Defect Engine
"""

from defect_engine.models import (
    BridgeRecord,
    Defect,
    DefectType,
    SeverityLevel,
)


# --------------------------------------------------
# Crack Detection
# --------------------------------------------------

def detect_crack(record: BridgeRecord) -> Defect | None:
    """
    Detect crack-related defects.
    """

    if (
        record.crack_propagation > 0.5
        and record.acoustic_emission > 30
    ):

        evidence = [
            f"Crack propagation = {record.crack_propagation:.3f} mm",
            f"Acoustic emission = {record.acoustic_emission:.2f}",
        ]

        return Defect(
            defect_id=f"CRACK-{record.timestamp}",
            defect_type=DefectType.CRACK,
            severity=SeverityLevel.HIGH,
            confidence=85.0,
            evidence=evidence,
            recommendation="Immediate structural inspection recommended.",
        )

    return None


# --------------------------------------------------
# Corrosion Detection
# --------------------------------------------------

def detect_corrosion(record: BridgeRecord) -> Defect | None:
    """
    Detect corrosion.
    """

    if record.corrosion_level > 40:

        evidence = [
            f"Corrosion level = {record.corrosion_level:.2f}%"
        ]

        return Defect(
            defect_id=f"CORR-{record.timestamp}",
            defect_type=DefectType.CORROSION,
            severity=SeverityLevel.MEDIUM,
            confidence=80.0,
            evidence=evidence,
            recommendation="Inspect affected area for corrosion.",
        )

    return None


# --------------------------------------------------
# Fatigue Detection
# --------------------------------------------------

def detect_fatigue(record: BridgeRecord) -> Defect | None:
    """
    Detect fatigue damage.
    """

    if record.fatigue_accumulation > 0.70:

        evidence = [
            f"Fatigue accumulation = {record.fatigue_accumulation:.3f}"
        ]

        return Defect(
            defect_id=f"FAT-{record.timestamp}",
            defect_type=DefectType.FATIGUE,
            severity=SeverityLevel.HIGH,
            confidence=82.0,
            evidence=evidence,
            recommendation="Monitor fatigue progression.",
        )

    return None


# --------------------------------------------------
# Structural Risk
# --------------------------------------------------

def detect_structural_risk(record: BridgeRecord) -> Defect | None:
    """
    Detect critical structural deterioration.
    """

    if (
        record.structural_health_index < 0.50
        and record.probability_of_failure > 0.60
    ):

        evidence = [
            f"SHI = {record.structural_health_index:.2f}",
            f"PoF = {record.probability_of_failure:.2f}",
        ]

        return Defect(
            defect_id=f"RISK-{record.timestamp}",
            defect_type=DefectType.UNKNOWN,
            severity=SeverityLevel.CRITICAL,
            confidence=95.0,
            evidence=evidence,
            recommendation="Immediate engineering assessment required.",
        )

    return None


# --------------------------------------------------
# Run All Rules
# --------------------------------------------------

def detect_defects(record: BridgeRecord) -> list[Defect]:
    """
    Run every rule against one bridge record.
    """

    defects = []

    for detector in (
        detect_crack,
        detect_corrosion,
        detect_fatigue,
        detect_structural_risk,
    ):

        defect = detector(record)

        if defect is not None:
            defects.append(defect)

    return defects

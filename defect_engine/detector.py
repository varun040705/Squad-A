"""
detector.py

Runs the complete defect detection pipeline.

Author: Sai Varun
Project: OX1 - Defect Engine
"""

from defect_engine.models import (
    BridgeRecord,
    DefectDetectionResult,
)

from defect_engine.rules import detect_defects


def run_defect_detector(
    records: list[BridgeRecord],
) -> DefectDetectionResult:
    """
    Run defect detection on every bridge record.
    """

    detected_defects = []

    for record in records:

        defects = detect_defects(record)

        detected_defects.extend(defects)

    return DefectDetectionResult(
        total_records=len(records),
        total_defects=len(detected_defects),
        defects=detected_defects,
    )

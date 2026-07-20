"""
engine.py

Integrates the Squad H Context Engine and Defect Detection Engine.

Author : Sai Varun
Project : OX1 Structural Health Monitoring
"""

from squad_h.models import AcousticEmissionContext
from squad_h.aggregate_engine import run_aggregate_ae

from defect_engine.loader import load_bridge_dataset
from defect_engine.detector import run_defect_detector
from defect_engine.models import DefectDetectionResult

from integration.models import InspectionContext


def build_inspection_context(
    context: AcousticEmissionContext,
    defects: DefectDetectionResult,
) -> InspectionContext:
    """
    Merge AE Context and Defect Detection output.
    """
    return InspectionContext(
        context=context,
        defects=defects,
    )


def run_complete_inspection(
    csv_path: str,
    inspection_id: str = "AE-CSV-001",
    element_ref: str = "BRIDGE-DT-01",
) -> InspectionContext:
    """
    Complete inspection pipeline.

    Steps
    -----
    1. Load bridge dataset.
    2. Run Aggregate AE Context Engine.
    3. Run Defect Detection.
    4. Merge results.

    Returns
    -------
    InspectionContext
    """

    # -------------------------
    # Load Dataset
    # -------------------------
    records = load_bridge_dataset(csv_path)

    # -------------------------
    # AE Context Engine
    # -------------------------
    context = run_aggregate_ae(
        inspection_id=inspection_id,
        element_ref=element_ref,
        csv_path=csv_path,
    )

    # -------------------------
    # Defect Detection
    # -------------------------
    defects = run_defect_detector(records)

    # -------------------------
    # Merge Results
    # -------------------------
    inspection = build_inspection_context(
        context=context,
        defects=defects,
    )

    return inspection
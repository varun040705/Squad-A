"""
engine.py

Integrates the Context Engine and Defect Engine.

Author: Sai Varun
Project: OX1
"""

from squad_h.models import AcousticEmissionContext

from defect_engine.models import (
    DefectDetectionResult,
)

from integration.models import InspectionContext


def build_inspection_context(

    context: AcousticEmissionContext,

    defects: DefectDetectionResult,

) -> InspectionContext:

    return InspectionContext(

        context=context,

        defects=defects,

    )
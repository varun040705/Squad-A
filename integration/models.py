"""
models.py

Combines the Context Engine and Defect Engine outputs.

Author: Sai Varun
Project: OX1
"""

from pydantic import BaseModel

from squad_h.models import AcousticEmissionContext
from defect_engine.models import DefectDetectionResult


class InspectionContext(BaseModel):

    context: AcousticEmissionContext

    defects: DefectDetectionResult

from pydantic import BaseModel, Field
from typing import List

class PointSchema(BaseModel):
    id: str = Field(..., description="Unique label for point measurement")
    width_mm: float = Field(..., gt=0, description="Crack width measurement in millimeters")

class InspectionRequest(BaseModel):
    element_type: str = Field(..., example="COLUMN")
    lighting: str = Field(..., example="DUSTY_SURFACE")
    accessibility: str = Field(..., example="REMOTE_DRONE")
    raw_points: List[PointSchema]

class ConsensusSchema(BaseModel):
    recommended_action: str
    agreement_strength: str

class PipelinePayloadSchema(BaseModel):
    element_type: str
    max_calibrated_width: float
    severity_grade: str
    consensus: ConsensusSchema

class InspectionResponse(BaseModel):
    status: str
    chat_response_summary: str
    pipeline_payload: PipelinePayloadSchema

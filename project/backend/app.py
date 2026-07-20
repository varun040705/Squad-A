"""
FastAPI Backend


Project : OX1 Structural Health Monitoring

Runs:
    uvicorn backend.app:app --reload
"""

from fastapi import FastAPI
from pydantic import BaseModel

from squad_h.aggregate_engine import run_aggregate_ae
from defect_engine.loader import load_bridge_dataset
from defect_engine.detector import run_defect_detector
from integration.engine import run_complete_inspection

app = FastAPI(
    title="OX1 Structural Health Monitoring API",
    version="1.0.0"
)


class AnalysisRequest(BaseModel):
    dataset_path: str
    inspection_id: str = "AE-001"
    element_ref: str = "C-07"


@app.get("/")
def home():

    return {
        "message": "OX1 API Running"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


@app.post("/analyze")
def analyze(request: AnalysisRequest):

    result = run_complete_inspection(
        csv_path=request.dataset_path,
        inspection_id=request.inspection_id,
        element_ref=request.element_ref,
    )

    return result.model_dump()
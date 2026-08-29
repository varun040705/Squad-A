"""
Surface Resistivity & Structural Intelligence API Server (FastAPI)

Runs:
    python -m uvicorn server:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

from modules.electric.surface_resistivity import (
    run_resistivity_engine,
    SurfaceResistivityInput,
    SurfaceResistivityContext
)
from modules.ndt.rebound_upv import (
    run_ndt_engine,
    ReboundUPVInput,
    ReboundUPVContext
)
from modules.dimensional.inspection import (
    run_dimensional_engine,
    DimensionalInspectionInput,
    DimensionalInspectionContext
)
from modules.survey.qa import (
    run_survey_engine,
    SurveyQAInput,
    SurveyQAContext
)
from modules.laboratory.testing import (
    run_laboratory_engine,
    LaboratoryTestingInput,
    LaboratoryTestingContext
)
from modules.geotechnical.qa import (
    run_geotechnical_engine,
    GeotechnicalQAInput,
    GeotechnicalQAContext
)
from modules.shm.monitoring import (
    run_shm_engine,
    SHMMonitoringInput,
    SHMMonitoringContext
)
from modules.forensics.investigation import (
    run_forensics_engine,
    ForensicsInvestigationInput,
    ForensicsInvestigationContext
)

app = FastAPI(
    title="OX1 Structural Intelligence API Platform",
    description="Comprehensive API for NDT, Durability, Structural QA, Survey, Lab Testing, Geotechnical, SHM, and Forensics",
    version="2.0.0"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": "OX1 Structural Intelligence Platform API",
        "docs": "http://localhost:8000/docs",
        "status": "online",
        "modules": [
            "electric", "ndt", "dimensional", "survey",
            "laboratory", "geotechnical", "shm", "forensics"
        ]
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


# 1. Electric / Surface Resistivity
@app.post("/api/v1/electric/surface-resistivity", response_model=SurfaceResistivityContext)
def calculate_surface_resistivity(payload: SurfaceResistivityInput):
    try:
        return run_resistivity_engine(payload.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 2. NDT / Rebound Hammer & UPV
@app.post("/api/v1/ndt/rebound-upv", response_model=ReboundUPVContext)
def calculate_rebound_upv(payload: ReboundUPVInput):
    try:
        return run_ndt_engine(payload.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 3. Dimensional / Clearance Cover & Floor Flatness
@app.post("/api/v1/dimensional/inspection", response_model=DimensionalInspectionContext)
def calculate_dimensional_inspection(payload: DimensionalInspectionInput):
    try:
        return run_dimensional_engine(payload.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 4. Survey / Plumbness & Settlement
@app.post("/api/v1/survey/qa", response_model=SurveyQAContext)
def calculate_survey_qa(payload: SurveyQAInput):
    try:
        return run_survey_engine(payload.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 5. Laboratory / Compressive & Split-Tensile Testing
@app.post("/api/v1/laboratory/testing", response_model=LaboratoryTestingContext)
def calculate_laboratory_testing(payload: LaboratoryTestingInput):
    try:
        return run_laboratory_engine(payload.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 6. Geotechnical / SPT & Terzaghi Bearing Capacity
@app.post("/api/v1/geotechnical/qa", response_model=GeotechnicalQAContext)
def calculate_geotechnical_qa(payload: GeotechnicalQAInput):
    try:
        return run_geotechnical_engine(payload.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 7. SHM / Mass Concrete Thermal & Stress-Strain
@app.post("/api/v1/shm/monitoring", response_model=SHMMonitoringContext)
def calculate_shm_monitoring(payload: SHMMonitoringInput):
    try:
        return run_shm_engine(payload.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 8. Forensics / Carbonation & Chloride Ingress
@app.post("/api/v1/forensics/investigation", response_model=ForensicsInvestigationContext)
def calculate_forensics_investigation(payload: ForensicsInvestigationInput):
    try:
        return run_forensics_engine(payload.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

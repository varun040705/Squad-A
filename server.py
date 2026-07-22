"""
Surface Resistivity API Server (FastAPI)

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

app = FastAPI(
    title="OX1 Surface Resistivity API",
    description="API for Concrete Surface Resistivity (AASHTO T 358) and Half-Cell Corrosion Risk (ASTM C876)",
    version="1.0.0"
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
        "service": "OX1 Surface Resistivity API",
        "docs": "http://localhost:8000/docs",
        "status": "online"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/api/v1/electric/surface-resistivity", response_model=SurfaceResistivityContext)
def calculate_surface_resistivity(payload: SurfaceResistivityInput):
    """
    Calculate corrected resistivity, chloride risk, half-cell corrosion risk, and quality flags.
    """
    try:
        context = run_resistivity_engine(payload.model_dump())
        return context
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

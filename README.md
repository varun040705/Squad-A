# OX1 Structural Health Monitoring

AI-powered Structural Health Monitoring system developed for bridge inspection.

The project combines:

- Acoustic Emission (AE) Context Engine (Squad H)
- Defect Detection Engine
- Integration Engine
- FastAPI Backend

Author: Sai Varun

---

# Project Architecture

```
                   Bridge Digital Twin Dataset (CSV)
                                │
                                ▼
                    defect_engine.loader
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
        Squad H Context Engine          Defect Detection
        (Aggregate AE Engine)              Engine
                │                               │
                ▼                               ▼
      AcousticEmissionContext         DefectDetectionResult
                │                               │
                └───────────────┬───────────────┘
                                ▼
                     Integration Engine
                                │
                                ▼
                     InspectionContext
                                │
                                ▼
                         FastAPI Backend
                                │
                                ▼
                         JSON REST API
```

---

# Folder Structure

```
project/
│
├── backend/
│   └── app.py
│
├── squad_h/
│   ├── aggregate_engine.py
│   ├── ae_h1.py
│   ├── ae_h2.py
│   ├── ae_h3.py
│   ├── models.py
│   ├── config.py
│   └── engine.py
│
├── defect_engine/
│   ├── loader.py
│   ├── detector.py
│   ├── rules.py
│   ├── models.py
│   └── enums.py
│
├── integration/
│   ├── engine.py
│   └── models.py
│
├── datasets/
│   └── bridge_digital_twin_dataset.csv
│
├── tests/
│
├── requirements.txt
│
└── README.md
```

---

# Modules

---

## 1. Squad H

Location

```
project/squad_h
```

Purpose

Processes Acoustic Emission data and builds the structural context.

Pipeline

```
CSV
 ↓
Aggregate Loader
 ↓
Trend Analysis
 ↓
Localization
 ↓
Load History
 ↓
Context Builder
 ↓
AcousticEmissionContext
```

Main Files

```
aggregate_engine.py

Main entry point for aggregate AE dataset

↓

ae_h2.py

Trend Analysis

↓

ae_h3.py

Context Builder

↓

models.py

Pydantic Models
```

Output

```
AcousticEmissionContext
```

---

## 2. Defect Engine

Location

```
project/defect_engine
```

Purpose

Detects structural defects from the bridge dataset.

Pipeline

```
CSV

↓

loader.py

↓

BridgeRecord

↓

rules.py

↓

Detected Defects

↓

DefectDetectionResult
```

Main Files

```
loader.py

Loads dataset

detector.py

Runs complete detection

rules.py

Contains all defect rules

models.py

Pydantic models
```

Output

```
DefectDetectionResult
```

---

## 3. Integration Engine

Location

```
project/integration
```

Purpose

Combines both engines.

Pipeline

```
Context Engine

+

Defect Engine

↓

InspectionContext
```

Main File

```
engine.py
```

Output

```
InspectionContext
```

---

## 4. Backend

Location

```
project/backend
```

Purpose

Expose APIs using FastAPI.

Routes

```
GET /

GET /health

POST /analyze
```

---

# API

---

## GET /

Returns

```json
{
  "message":"OX1 API Running"
}
```

---

## GET /health

Returns

```json
{
    "status":"healthy"
}
```

---

## POST /analyze

Input

```json
{
  "dataset_path":"datasets/bridge_digital_twin_dataset.csv",
  "inspection_id":"AE-001",
  "element_ref":"Bridge-C1"
}
```

Returns

```json
{
   "context":{
      ...
   },
   "defects":{
      ...
   }
}
```

---

# Dataset

Current dataset

```
datasets/
    bridge_digital_twin_dataset.csv
```

Required columns

```
Timestamp

Acoustic_Emissions_levels

Crack_Propagation_mm

Corrosion_Level_percent

Fatigue_Accumulation_au

Structural_Health_Index_SHI

Anomaly_Detection_Score

Probability_of_Failure_PoF

Maintenance_Alert
```

---

# Installation

Clone repository

```bash
git clone <repository-url>

cd project
```

Create virtual environment

Windows

```bash
python -m venv venv
```

Activate

Windows

```bash
venv\Scripts\activate
```

Linux/Mac

```bash
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# Run Backend

Start FastAPI

```bash
python -m uvicorn backend.app:app --reload
```

Server

```
http://127.0.0.1:8000
```

Swagger Documentation

```
http://127.0.0.1:8000/docs
```

Redoc

```
http://127.0.0.1:8000/redoc
```

---

# Project Workflow

```
User

↓

POST /analyze

↓

Backend

↓

Integration Engine

↓

AE Context Engine

↓

Defect Engine

↓

Merge Results

↓

JSON Response
```

---

# Data Flow

```
CSV

↓

BridgeRecord

↓

Defect Detection

↓

DefectDetectionResult

────────────────────

CSV

↓

Aggregate AE

↓

Trend Analysis

↓

Localization

↓

Context Builder

↓

AcousticEmissionContext

────────────────────

↓

Integration Engine

↓

InspectionContext

↓

API Response
```

---

# Team Responsibilities

---

## Squad H

Responsible for

- Aggregate Engine
- Context Builder
- Trend Analysis
- Localization
- Load History
- AE Models

Files

```
squad_h/*
```

---

## Defect Engine Team

Responsible for

- Detection Rules
- New Defect Types
- Dataset Parsing
- Defect Models

Files

```
defect_engine/*
```

---

## Backend Team

Responsible for

- FastAPI
- Authentication (future)
- API Versioning
- Error Handling
- Deployment

Files

```
backend/*
```

---

## Integration Team

Responsible for

- Engine Coordination
- Combining Outputs
- Future LLM Integration
- Report Generation

Files

```
integration/*
```

---

# Coding Guidelines

- Follow PEP 8.
- Use type hints for all public functions.
- Keep business logic inside the engine modules.
- Avoid duplicate implementations.
- Reuse existing functions whenever possible.
- Validate all incoming data using Pydantic models.
- Write unit tests for any new feature.

---

# Future Roadmap

- PDF report generation
- LLM-powered inspection summaries
- Dashboard UI
- Real-time sensor streaming
- Multi-bridge support
- Database integration
- Authentication & user management
- Docker deployment
- CI/CD with GitHub Actions

---

# Tech Stack

Backend

- Python
- FastAPI
- Pydantic

Data Processing

- Pandas
- NumPy

API

- Uvicorn

Documentation

- Swagger UI
- ReDoc

---

# Contributors

Project Lead

Sai Varun

Contributors

1.Sujith
2.Sathya Priya
3.Vaishnavi


---

# License

Internal Project

OX1 Structural Health Monitoring

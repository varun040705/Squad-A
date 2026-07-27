# 🏢 NDT Concrete Structural Inspection Engine (UPV Pipeline)

An AI-driven Non-Destructive Testing (NDT) analysis engine and web application for structural concrete integrity assessment. By leveraging **Ultrasonic Pulse Velocity (UPV)** measurements, telemetry data, and visual defect observations, this system automates defect detection, calculates structural degradation probability, and generates consensus structural reports.

---

## 📌 Project Overview

Non-Destructive Testing (NDT) using Ultrasonic Pulse Velocity (UPV) assesses concrete quality by measuring the transit time and velocity of high-frequency sound waves passing through structural elements. 

This repository provides an end-to-end full-stack solution featuring:
* **FastAPI Backend:** Modular evaluation pipeline, data validation, and automated risk scoring.
* **Next.js Dashboard:** An interactive visual test deck for inputting telemetry data and viewing structural health assessments.
* **Multi-Squad Pipeline Architecture:** Context processing, automated visual defect mapping (cracks, honeycombing, voids), and fallback evaluation engines.

---

## 🧮 NDT Evaluation Criteria

The system evaluates concrete quality according to standardized UPV velocity thresholds:

| Pulse Velocity ($km/s$) | Concrete Quality Grade | Structural Interpretation |
| :--- | :--- | :--- |
| **> 4.5** | **Excellent** | Intact, high-density concrete with no significant micro-cracking. |
| **3.5 - 4.5** | **Good** | Standard quality concrete; minor surface porosity permitted. |
| **3.0 - 3.5** | **Medium / Fair** | Potential micro-cracks, mild honeycombing, or localized voiding. |
| **2.0 - 3.0** | **Poor** | Severe void formation, internal cracking, or delamination present. |
| **< 2.0** | **Very Poor** | Critical structural degradation / major internal hollow spots. |

---

## 🏗️ System Architecture

```text
upv_project/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── routes/   # Inspection routes & analysis endpoints
│   │   ├── models/           # Pydantic schemas & telemetry models
│   │   ├── services/         # Engineering calculations & ML inference logic
│   │   └── main.py           # FastAPI entry point & CORS configuration
│   └── requirements.txt
│
├── frontend/                 # Next.js Application
│   ├── src/
│   │   ├── app/              # Dashboard pages & analysis forms
│   │   └── components/       # Telemetry inputs & report cards
│   └── package.json
│
└── .gitignore                # Environment & cache management

# OX1 NDT & Structural Intelligence Platform
## Complete Architecture, Workflows, Formulas, & Developer PR Guide

> **Single Source of Truth**: This document details the **OX1 Structural Intelligence Platform (Squad A / Member 1)**. It covers the full spectrum of 8 engineering domains: Durability, NDT, Dimensional QA, Surveying, Lab Testing, Geotechnical Analysis, Structural Health Monitoring (SHM), and Forensics.

---

## 1. System Overview & Domain Coverage

The **Structural Intelligence Engine** automates engineering calculations, quality control threshold checks, and dynamic confidence scoring across 8 standardized structural engineering domains:

1. **Electric / Surface Resistivity (AASHTO T 358 & ASTM C876)**: Concrete surface resistivity, curing/Arrhenius temperature corrections, chloride penetrability, and half-cell corrosion risk mapping.
2. **NDT / Rebound Hammer & UPV (ASTM C805 & ASTM C597)**: Rebound hammer outlier filtering (6-unit rule), Ultrasonic Pulse Velocity wave velocity classification, and SonReb combined strength estimation.
3. **Dimensional Inspection (ACI 117 & ASTM E1155)**: Rebar clearance cover tolerance checks and Floor Flatness ($F_F$) / Levelness ($F_L$) numbers.
4. **Survey QA (ACI 117 & ISO 4463)**: Out-of-plumbness ratio ($\delta/H$), top offset drift tolerances, and foundation settlement velocity alerts.
5. **Laboratory Testing (ASTM C39, ASTM C496 & ACI 318)**: Concrete cylinder compressive strength, splitting tensile strength, $L/D$ ratio corrections, and ACI 318-19 acceptance evaluation.
6. **Geotechnical QA (ASTM D1586 & Terzaghi)**: Standard Penetration Test ($N_{60}$, $(N_1)_{60}$) corrections and Terzaghi shallow footing ultimate/allowable bearing capacity.
7. **Structural Health Monitoring - SHM (ACI 207.2R & Hooke's Law)**: Mass concrete core-to-surface thermal differential ($\Delta T$) cracking risk and elastic stress-strain yield ratio.
8. **Forensics & Investigation (Carbonation & Fick's 2nd Law)**: Carbonation depth rate ($d_c = k\sqrt{t}$) projections and Fick's 2nd Law chloride diffusion solution.

---

## 2. Directory & API Endpoint Mapping

| Domain | FastAPI Endpoint | Backend Module | Test File | Frontend Feature Path |
| :--- | :--- | :--- | :--- | :--- |
| **Electric** | `POST /api/v1/electric/surface-resistivity` | [`surface_resistivity.py`](file:///c:/Users/binee/OneDrive/Desktop/Surface%20resistivity/modules/electric/surface_resistivity.py) | [`test_surface_resistivity.py`](file:///c:/Users/binee/OneDrive/Desktop/Surface%20resistivity/tests/test_surface_resistivity.py) | `frontend/src/features/surface-resistivity/` |
| **NDT** | `POST /api/v1/ndt/rebound-upv` | [`rebound_upv.py`](file:///c:/Users/binee/OneDrive/Desktop/Surface%20resistivity/modules/ndt/rebound_upv.py) | [`test_ndt.py`](file:///c:/Users/binee/OneDrive/Desktop/Surface%20resistivity/tests/test_ndt.py) | `frontend/src/features/ndt/` |
| **Dimensional** | `POST /api/v1/dimensional/inspection` | [`inspection.py`](file:///c:/Users/binee/OneDrive/Desktop/Surface%20resistivity/modules/dimensional/inspection.py) | [`test_dimensional.py`](file:///c:/Users/binee/OneDrive/Desktop/Surface%20resistivity/tests/test_dimensional.py) | `frontend/src/features/dimensional/` |
| **Survey** | `POST /api/v1/survey/qa` | [`qa.py`](file:///c:/Users/binee/OneDrive/Desktop/Surface%20resistivity/modules/survey/qa.py) | [`test_survey.py`](file:///c:/Users/binee/OneDrive/Desktop/Surface%20resistivity/tests/test_survey.py) | `frontend/src/features/survey/` |
| **Laboratory** | `POST /api/v1/laboratory/testing` | [`testing.py`](file:///c:/Users/binee/OneDrive/Desktop/Surface%20resistivity/modules/laboratory/testing.py) | [`test_laboratory.py`](file:///c:/Users/binee/OneDrive/Desktop/Surface%20resistivity/tests/test_laboratory.py) | `frontend/src/features/laboratory/` |
| **Geotechnical**| `POST /api/v1/geotechnical/qa` | [`qa.py`](file:///c:/Users/binee/OneDrive/Desktop/Surface%20resistivity/modules/geotechnical/qa.py) | [`test_geotechnical.py`](file:///c:/Users/binee/OneDrive/Desktop/Surface%20resistivity/tests/test_geotechnical.py) | `frontend/src/features/geotechnical/` |
| **SHM** | `POST /api/v1/shm/monitoring` | [`monitoring.py`](file:///c:/Users/binee/OneDrive/Desktop/Surface%20resistivity/modules/shm/monitoring.py) | [`test_shm.py`](file:///c:/Users/binee/OneDrive/Desktop/Surface%20resistivity/tests/test_shm.py) | `frontend/src/features/shm/` |
| **Forensics** | `POST /api/v1/forensics/investigation` | [`investigation.py`](file:///c:/Users/binee/OneDrive/Desktop/Surface%20resistivity/modules/forensics/investigation.py) | [`test_forensics.py`](file:///c:/Users/binee/OneDrive/Desktop/Surface%20resistivity/tests/test_forensics.py) | `frontend/src/features/forensics/` |

---

## 3. Mathematical Formulas Summary

### 3.1. Rebound Hammer Outlier Filtering (ASTM C805)
$$\text{Discard reading } R_i \text{ if } |R_i - \bar{R}_{\text{raw}}| > 6.0$$
$$\text{Re-calculate } \bar{R}_{\text{filtered}} = \frac{1}{m} \sum_{i=1}^m R_i^{\text{valid}}$$
$$\text{Estimated } f'_c = 0.025 \cdot (\bar{R}_{\text{filtered}} + \text{angle\_corr})^2 + 0.4 \cdot (\bar{R}_{\text{filtered}} + \text{angle\_corr}) - 5.0$$

### 3.2. UPV Pulse Velocity & SonReb (ASTM C597)
$$V = \frac{L \cdot 10^6}{t_{\mu\text{s}}} \quad (\text{m/s})$$
$$\text{SonReb Combined } f'_c = 1.2 \times 10^{-9} \cdot (V^{2.6}) \cdot (\bar{R}^{1.4}) \quad (\text{MPa})$$

### 3.3. Floor Flatness ($F_F$) & Levelness ($F_L$) (ASTM E1155)
$$F_F = \frac{4.57}{S_q}, \quad F_L = \frac{4.57}{S_z}$$
Where $S_q$ is standard deviation of adjacent elevation differences $d_i = y_{i+1} - y_i$, and $S_z$ is standard deviation of 2-step differences $z_i = y_{i+2} - y_i$.

### 3.4. Verticality & Plumbness (ACI 117)
$$\text{Resultant Drift } \delta = \sqrt{\delta_x^2 + \delta_y^2} \quad (\text{mm})$$
$$\text{Drift Ratio} = \frac{\delta}{H \cdot 1000}, \quad \delta_{\text{allowable}} = \min\left(\frac{H \cdot 1000}{500}, \; 150\text{ mm}\right)$$

### 3.5. Compressive & Splitting Tensile Strength (ASTM C39 / C496)
$$f_c = \frac{P \cdot 1000}{A} \times f_{L/D}, \quad f_t = \frac{2 P \cdot 1000}{\pi L d}$$

### 3.6. SPT $N_{60}$ & Terzaghi Bearing Capacity
$$N_{60} = N_{\text{raw}} \cdot \frac{C_E \cdot C_R \cdot C_S \cdot C_B}{0.60}$$
$$q_{\text{ult}} = c N_c s_c + q N_q + 0.5 \gamma B N_\gamma s_\gamma, \quad q_{\text{all}} = \frac{q_{\text{ult}}}{FS}$$

### 3.7. SHM Thermal Differential & Elastic Stress
$$\Delta T = T_{\text{core}} - T_{\text{surface}} \quad (\text{Allowable Limit } \le 20^\circ\text{C})$$
$$\sigma = \frac{E \cdot \epsilon_{\mu\text{e}}}{1000} \quad (\text{MPa}), \quad \text{Yield Ratio} = \frac{\sigma}{f_y} \times 100\%$$

### 3.8. Carbonation Rate & Fick's 2nd Law Chloride Diffusion
$$d_c = k\sqrt{t} \implies k = \frac{d_c}{\sqrt{t}}, \quad t_{\text{depass}} = \left(\frac{\text{cover}}{k}\right)^2$$
$$C(x,t) = C_s \cdot \left[1 - \text{erf}\left(\frac{x}{2\sqrt{D t}}\right)\right]$$

---

## 4. Dual Engine Synchronization Hazard (CRITICAL FOR PRs!)

> [!CAUTION]
> **Twin Engine Architecture**: Every calculation engine is implemented in **Python** (backend `modules/`) and mirrored in **TypeScript** (frontend `features/`).
> **When submitting a PR**, you MUST update both Python and TypeScript implementations in tandem.

---

## 5. Developer Verification & Test Execution

Run the complete test suite:
```bash
python -m pytest
```
Verify frontend build:
```bash
cd frontend
npm run lint
npm run build
```
---
*Document Version: 2.0.0 — Squad A Member 1 Structural Intelligence System*

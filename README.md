# Image-to-BIM — T1.4 Evaluation Harness

## Overview

T1.4 is the Evaluation Harness and Accuracy Testing component of the
Image-to-BIM project.

It compares:

- Ground-truth architectural elements
- Predicted/model-generated elements

and calculates evaluation metrics for:

- Walls
- Doors
- Windows
- Rooms
- Scale

The evaluator supports per-level, per-plan, and dataset-level reporting.

---

## Evaluation Metrics

### Precision

Measures how many predicted elements are correct.

### Recall

Measures how many ground-truth elements were detected.

### F1-score

Combines precision and recall into a single score.

### Scale Accuracy

Measures the difference between ground-truth and predicted
millimetres-per-pixel values.

### Overall Element F1

Provides one summary score across:

- Walls
- Doors
- Windows
- Rooms

---

## Project Structure

```text
IMAGE_TO_BIM_T1_4_EVALUATION/
│
├── evaluator/
│   ├── __init__.py
│   ├── config.py
│   ├── ground_truth_adapter.py
│   ├── main.py
│   ├── matching.py
│   ├── metrics.py
│   ├── report.py
│   ├── scale_metrics.py
│   └── validator.py
│
├── sample_data/
│   ├── ground_truth.json
│   └── prediction.json
│
├── reports/
│   ├── ground_truth_evaluation.json
│   └── dataset_evaluation_report.json
│
├── tests/
│   ├── __init__.py
│   └── test_evaluator.py
│
└── README.md
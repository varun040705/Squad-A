# Task T1.2: Ground-Truth Annotation Pipeline

This module implements the complete ground-truth annotation pipeline for **Task T1.2**, part of Team 1's dataset engineering stream.

---

## 1. Ground-Truth Category Taxonomy

The dataset standardizes architectural annotations into **5 essential classes**:

| Category ID | Name | Supercategory | Geometry Type | Description |
| :---: | :---: | :---: | :---: | :--- |
| **1** | `wall` | architectural | Polygon / BBox | Exterior structural and interior partition walls |
| **2** | `door` | architectural | Polygon / BBox | Single swing, double, sliding doors & openings |
| **3** | `window` | architectural | Polygon / BBox | Exterior glazing and window openings |
| **4** | `room` | space | Polygon / BBox | Bounded enclosed rooms (living, bed, bath, kitchen) |
| **5** | `dimension` | annotation | Polygon / BBox | Measurement lines, ticks, and text numerals |

All noise categories (`-_-`, `background`) have been purged.

---

## 2. Dataset Metrics Across Splits

Generated across the entire dataset of **1,461 floor plans**:

| Split | Images | Walls | Doors | Windows | Rooms (NEW) | Dimensions (NEW) | Total Annotations | Ground-Truth File |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Test** | 146 | 10,441 | 2,568 | 4,808 | 1,131 | 9,929 | **28,877** | `floor-plan.v1i.coco/test/_ground_truth.coco.json` |
| **Valid** | 292 | 18,860 | 5,128 | 20,334 | 2,042 | 19,419 | **65,783** | `floor-plan.v1i.coco/valid/_ground_truth.coco.json` |
| **Train** | 1,023 | 69,974 | 18,241 | 50,851 | 7,431 | 68,266 | **214,763** | `floor-plan.v1i.coco/train/_ground_truth.coco.json` |
| **Total** | **1,461** | **99,275** | **25,937** | **75,993** | **10,604** | **97,614** | **309,423** | — |

---

## 3. Module Architecture

```
ground_truth/
├── __init__.py
├── cleaner.py             # Removes noise tags and validates polygon bounding boxes
├── room_extractor.py      # Topological morphological room polygon segmentation engine
├── dimension_extractor.py # Line and text dimension callout extractor
├── builder.py             # Orchestrator building unified COCO ground truth
├── visualizer.py          # Visual inspection tool rendering 5-layer colored overlays
├── exporter.py            # Converts COCO flat format to intermediate schema for Member 3
└── samples/               # Rendered visual overlay proofs
```

---

## 4. Usage Commands

### Run Full Test Suite
```bash
pytest tests/test_ground_truth.py -v
```

### Rebuild Ground-Truth Dataset
```bash
python -m ground_truth.builder
```

### Generate Visual Inspection Proofs
```bash
python -c "from ground_truth.visualizer import visualize_sample; visualize_sample('floor-plan.v1i.coco/test/_ground_truth.coco.json', 'floor-plan.v1i.coco/test', image_index=0)"
```

### Export Intermediate JSON for Member 3 (T1.3)
```bash
python -c "from ground_truth.exporter import export_intermediate_ground_truth; export_intermediate_ground_truth('floor-plan.v1i.coco/test/_ground_truth.coco.json', 'ground_truth/ground_truth_test.json')"
```

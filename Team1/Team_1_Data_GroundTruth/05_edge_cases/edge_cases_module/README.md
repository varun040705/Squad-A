# Task T1.5: Edge-Case Set Curation

Curates a stress-test subset of the T1.1 image dataset by flagging images
that are relatively harder along a few cheap pixel-level signals: sharpness,
visual clutter, and rotation/skew.

---

## IMPORTANT LIMITATION

This module can only surface images that are *relatively* harder within
whatever batch you feed it. If your source folder is all clean, uniform CAD
renders (as T1.1's initial batch is), the resulting "edge cases" are only
harder than their CAD peers -- **not genuinely difficult** in the real-world
sense the project plan calls for (perspective distortion, shadows, faded
scans, hand-drawn sketches, blurry phone photos). Getting real difficulty
variety requires sourcing actual scanned / photographed / hand-drawn images
into `01_raw_images/` first -- this module cannot manufacture it from CAD
alone.

---

## Module architecture

```
edge_cases/
├── __init__.py
├── metrics.py     # per-image heuristics: blur_var, edge_density, rotation_clean_frac, OCR-based has_text/has_dimensions
├── selector.py     # candidate selection: overall HARD difficulty + top-N per individual metric
├── curator.py       # orchestrator: compute -> bucket -> select -> copy -> write manifest
└── README.md
```

## Usage

```python
from edge_cases.curator import EdgeCaseCurator

curator = EdgeCaseCurator(
    source_dir="Team_1_Data_GroundTruth/01_raw_images/cad",
    output_dir="Team_1_Data_GroundTruth/05_edge_cases",
    top_n_per_criterion=20,   # tune to how large you want the set
)
manifest_rows = curator.run()
```

Or run directly:

```bash
python -m edge_cases.curator
```

This copies selected images into `output_dir` and writes
`edge_case_manifest.csv` there, with one row per selected image recording
which criteria flagged it (`reasons`) and its raw metric values, so the
selection is auditable rather than a black box.

## Selection criteria

An image is selected if it is EITHER:
- labeled overall `HARD` difficulty (combines quality + clutter + rotation), OR
- among the 20 blurriest images in the batch, OR
- among the 20 highest edge-density (busiest/most cluttered) images, OR
- among the 20 most rotated/skewed images

On the current T1.1 CAD batch (1,461 images), this selects **93 images**.

## Validated results (this run)

| Reason | Count |
|---|---|
| Overall HARD difficulty | 45 |
| Lowest sharpness | 20 |
| Highest clutter | 20 |
| Most rotated | 20 |
| **Total unique (with overlap)** | **93** |

## Next step

Once real scanned/photo/hand-drawn images are sourced into `01_raw_images/`,
rerun this module against the *combined* dataset (or per-subfolder) to get
edge cases that reflect genuine real-world difficulty, not just relative
CAD-batch outliers.

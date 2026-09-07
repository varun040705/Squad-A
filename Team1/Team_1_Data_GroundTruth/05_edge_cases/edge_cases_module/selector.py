"""
Edge-Case Candidate Selector for Task T1.5.
Selects a stress-test subset from a batch of scored images, tagging each
selected image with the reason(s) it was flagged.

------------------------------------------------------------------------------
ASSUMPTIONS / PLACEHOLDERS:

1. This selector can only surface images that are relatively harder within
   whatever batch it's given. If the input batch is all clean, uniform,
   high-resolution CAD renders (as in T1.1's initial CAD sourcing pass),
   the resulting "edge cases" are only relatively harder than their peers --
   NOT genuinely difficult in the real-world sense the project plan
   describes (perspective distortion, shadows, faded scans, hand-drawn
   sketches, blurry phone photos). Real difficulty variety has to come from
   sourcing actual scanned/photographed/hand-drawn images -- this selector
   cannot manufacture it from CAD renders alone.

2. `top_n_per_criterion` is an arbitrary choice (default 20), not derived
   from any statistical rule. Tune it to how large you want the edge-case
   set to be.
------------------------------------------------------------------------------
"""

from typing import Dict, List
from collections import defaultdict

from metrics import ImageMetrics


def select_edge_cases(
    metrics: List[ImageMetrics],
    difficulty: Dict[str, str],
    top_n_per_criterion: int = 20,
) -> Dict[str, List[str]]:
    """
    Selects edge-case candidates as the union of:
      - every image already labeled overall HARD difficulty
      - the top_n_per_criterion images with lowest sharpness (blurriest)
      - the top_n_per_criterion images with highest edge density (busiest)
      - the top_n_per_criterion images with lowest rotation_clean_frac (most skewed)

    Returns {image_id: [reason, ...]} for every selected image. An image can
    have multiple reasons if it was flagged by more than one criterion.
    """
    reasons: Dict[str, List[str]] = defaultdict(list)

    for image_id, label in difficulty.items():
        if label == "HARD":
            reasons[image_id].append("difficulty=HARD")

    by_blur = sorted(metrics, key=lambda m: m.blur_var)
    by_edge = sorted(metrics, key=lambda m: -m.edge_density)
    by_rotation = sorted(metrics, key=lambda m: m.rotation_clean_frac)

    for m in by_blur[:top_n_per_criterion]:
        reasons[m.image_id].append("lowest_sharpness")
    for m in by_edge[:top_n_per_criterion]:
        reasons[m.image_id].append("highest_clutter")
    for m in by_rotation[:top_n_per_criterion]:
        reasons[m.image_id].append("most_rotated")

    return dict(reasons)

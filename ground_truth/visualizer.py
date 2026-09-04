"""
Visual Verification Tool for Task T1.2 Ground-Truth Annotations.
Renders high-resolution floor plans with color-coded polygon overlays for:
Walls (Blue), Doors (Orange), Windows (Green), Rooms (Purple), Dimensions (Red).
"""

import os
import json
from typing import Dict, Any, List, Optional
import cv2
import numpy as np

# Color scheme in BGR for OpenCV
CLASS_COLORS = {
    1: {"name": "Wall", "color": (255, 120, 30), "alpha": 0.55},       # Blue
    2: {"name": "Door", "color": (0, 140, 255), "alpha": 0.65},        # Orange
    3: {"name": "Window", "color": (50, 205, 50), "alpha": 0.65},      # Green
    4: {"name": "Room", "color": (220, 20, 180), "alpha": 0.28},       # Purple
    5: {"name": "Dimension", "color": (0, 0, 230), "alpha": 0.70},     # Red
}


def render_ground_truth_overlay(
    image: np.ndarray,
    annotations: List[Dict[str, Any]],
    include_labels: bool = True,
    line_thickness: int = 2
) -> np.ndarray:
    """
    Overlays color-coded polygon segmentations and labels onto a floor plan image.
    """
    overlay = image.copy()
    output = image.copy()

    # First pass: Fill room semi-transparent polygons
    for ann in annotations:
        cat_id = ann.get("category_id")
        if cat_id == 4:  # Room
            color_info = CLASS_COLORS[cat_id]
            for pts in ann.get("segmentation", []):
                if len(pts) >= 6:
                    poly = np.array(pts, dtype=np.int32).reshape((-1, 2))
                    cv2.fillPoly(overlay, [poly], color_info["color"])
                    
    # Blend room overlays
    cv2.addWeighted(overlay, 0.35, output, 0.65, 0, output)
    overlay = output.copy()

    # Second pass: Walls, Doors, Windows, Dimensions
    for ann in annotations:
        cat_id = ann.get("category_id")
        if cat_id in CLASS_COLORS and cat_id != 4:
            color_info = CLASS_COLORS[cat_id]
            for pts in ann.get("segmentation", []):
                if len(pts) >= 6:
                    poly = np.array(pts, dtype=np.int32).reshape((-1, 2))
                    cv2.fillPoly(overlay, [poly], color_info["color"])
                    cv2.polylines(output, [poly], isClosed=True, color=color_info["color"], thickness=line_thickness)

    # Blend structural overlays
    cv2.addWeighted(overlay, 0.60, output, 0.40, 0, output)

    # Draw Legend at top-left
    legend_x, legend_y = 25, 30
    cv2.rectangle(output, (legend_x - 10, legend_y - 20), (legend_x + 360, legend_y + 160), (245, 245, 245), -1)
    cv2.rectangle(output, (legend_x - 10, legend_y - 20), (legend_x + 360, legend_y + 160), (180, 180, 180), 1)

    cv2.putText(output, "T1.2 Ground-Truth Classes", (legend_x, legend_y), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (30, 30, 30), 2)
    y_offset = legend_y + 28
    for cat_id, info in CLASS_COLORS.items():
        # Draw color swatch
        cv2.rectangle(output, (legend_x, y_offset - 12), (legend_x + 22, y_offset + 4), info["color"], -1)
        cv2.rectangle(output, (legend_x, y_offset - 12), (legend_x + 22, y_offset + 4), (50, 50, 50), 1)
        # Text
        count = sum(1 for a in annotations if a.get("category_id") == cat_id)
        label_text = f"{info['name']} (Count: {count})"
        cv2.putText(output, label_text, (legend_x + 32, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (40, 40, 40), 1)
        y_offset += 24

    return output


def visualize_sample(
    coco_json_path: str,
    images_dir: str,
    output_dir: str = "ground_truth/samples",
    image_index: int = 0
) -> Optional[str]:
    """
    Renders and saves a verified visual sample for a specific floor plan.
    """
    os.makedirs(output_dir, exist_ok=True)
    with open(coco_json_path, "r", encoding="utf-8") as f:
        coco = json.load(f)

    if not coco.get("images"):
        return None

    img_info = coco["images"][image_index]
    img_path = os.path.join(images_dir, img_info["file_name"])
    if not os.path.exists(img_path):
        return None

    image = cv2.imread(img_path)
    anns = [a for a in coco.get("annotations", []) if a["image_id"] == img_info["id"]]

    rendered = render_ground_truth_overlay(image, anns)
    output_path = os.path.join(output_dir, f"gt_overlay_{image_index}_{img_info['file_name']}")
    cv2.imwrite(output_path, rendered)
    return output_path

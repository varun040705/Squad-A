"""
Dimension Ground-Truth Extractor for Task T1.2.
Detects architectural dimension lines, tick marks, and measurement text regions.
"""

import os
from typing import List, Dict, Any, Optional
import cv2
import numpy as np


def extract_dimensions(
    image_width: int,
    image_height: int,
    annotations: List[Dict[str, Any]],
    image_path: Optional[str] = None,
    min_dim_area: int = 18,
    max_dim_width: int = 250,
    max_dim_height: int = 150
) -> List[Dict[str, Any]]:
    """
    Extracts dimension markers, dimension lines, and measurement callouts.
    
    If the source image exists on disk, computer vision morphology is used to isolate
    drawing markings outside structural wall boundaries.
    If the image is not found, geometric dimension inferences from room spans are generated.
    
    Returns:
        List of COCO annotation dictionaries for dimensions (category_id: 5)
    """
    dimensions: List[Dict[str, Any]] = []
    
    if image_path and os.path.exists(image_path):
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            # Threshold dark drawing markings on white floor plan background
            _, bin_img = cv2.threshold(img, 205, 255, cv2.THRESH_BINARY_INV)
            
            # Create a mask of existing structural annotations (walls, doors, windows)
            struct_mask = np.zeros(img.shape, dtype=np.uint8)
            for ann in annotations:
                cat_id = ann.get("category_id")
                # Exclude structural components (walls=1, doors=2, windows=3)
                if cat_id in (1, 2, 3):
                    for pts in ann.get("segmentation", []):
                        if len(pts) >= 6:
                            poly = np.array(pts, dtype=np.int32).reshape((-1, 2))
                            cv2.fillPoly(struct_mask, [poly], 255)
                            
            # Dilate structural mask to mask out wall strokes and door swing arcs
            dilated_struct = cv2.dilate(struct_mask, np.ones((7, 7), np.uint8))
            non_structural = cv2.bitwise_and(bin_img, cv2.bitwise_not(dilated_struct))
            
            # Cluster dimension characters and line segments
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 5))
            clustered = cv2.morphologyEx(non_structural, cv2.MORPH_CLOSE, kernel)
            
            num_labels, _, stats, _ = cv2.connectedComponentsWithStats(clustered)
            
            for i in range(1, num_labels):
                x, y, w, h, area = stats[i]
                
                # Check for horizontal dimension lines, vertical dimension lines, or text callouts
                is_text = (10 <= w <= 140 and 6 <= h <= 50 and area >= min_dim_area)
                is_h_line = (25 <= w <= max_dim_width and 2 <= h <= 14 and area >= min_dim_area)
                is_v_line = (2 <= w <= 14 and 25 <= h <= max_dim_height and area >= min_dim_area)
                
                if (is_text or is_h_line or is_v_line) and w <= max_dim_width and h <= max_dim_height:
                    # Form standard 4-corner polygon
                    poly = [
                        float(x), float(y),
                        float(x + w), float(y),
                        float(x + w), float(y + h),
                        float(x), float(y + h)
                    ]
                    dim_type = "dimension_line" if (is_h_line or is_v_line) else "measurement_callout"
                    dimensions.append({
                        "category_id": 5,  # Standardized dimension class ID
                        "bbox": [round(float(x), 3), round(float(y), 3), round(float(w), 3), round(float(h), 3)],
                        "segmentation": [poly],
                        "area": round(float(area), 3),
                        "iscrowd": 0,
                        "dimension_type": dim_type
                    })
                    
    # Fallback / geometric inference if image file is not present
    if not dimensions:
        # Generate dimension bounding indicators from room perimeter spans
        room_anns = [a for a in annotations if a.get("category_id") == 4]
        for idx, room in enumerate(room_anns[:15]):  # limit to primary rooms
            rx, ry, rw, rh = room.get("bbox", [0, 0, 0, 0])
            if rw > 40 and rh > 40:
                # Top horizontal dimension span
                dx = rx
                dy = max(0.0, ry - 15.0)
                dw = rw
                dh = 6.0
                poly_h = [dx, dy, dx + dw, dy, dx + dw, dy + dh, dx, dy + dh]
                dimensions.append({
                    "category_id": 5,
                    "bbox": [round(dx, 3), round(dy, 3), round(dw, 3), round(dh, 3)],
                    "segmentation": [poly_h],
                    "area": round(dw * dh, 3),
                    "iscrowd": 0,
                    "dimension_type": "dimension_span"
                })
                
    return dimensions

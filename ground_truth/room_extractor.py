"""
Topological Room Ground-Truth Segmentation Engine for Task T1.2.
Detects enclosed architectural interior spaces bounded by walls and doors.
"""

from typing import List, Dict, Any, Tuple
import cv2
import numpy as np


def extract_rooms_from_annotations(
    image_width: int,
    image_height: int,
    annotations: List[Dict[str, Any]],
    min_room_area: float = 3000.0,
    max_room_area: float = 300000.0,
    gap_closure_kernel_size: int = 11,
    polygon_simplification_epsilon: float = 3.5,
) -> List[Dict[str, Any]]:
    """
    Extracts enclosed room spaces using morphological wall-closure and connected component analysis.
    
    Args:
        image_width: Width of the floor plan (e.g. 1920)
        image_height: Height of the floor plan (e.g. 1080)
        annotations: List of cleaned annotations containing walls (cat 1), doors (cat 2), windows (cat 3)
        min_room_area: Minimum pixel area to consider a valid room space
        max_room_area: Maximum pixel area for a single room
        gap_closure_kernel_size: Size of morphological kernel to bridge wall/door junctions
        polygon_simplification_epsilon: Douglas-Peucker simplification tolerance
        
    Returns:
        List of COCO annotation dictionaries for detected rooms (category_id: 4)
    """
    barrier_mask = np.zeros((image_height, image_width), dtype=np.uint8)
    
    # Rasterize structural boundaries (walls, doors, windows)
    for ann in annotations:
        cat_id = ann.get("category_id")
        # In standardized taxonomy: 1=wall, 2=door, 3=window
        if cat_id in (1, 2, 3):
            for pts in ann.get("segmentation", []):
                if len(pts) >= 6:
                    poly = np.array(pts, dtype=np.int32).reshape((-1, 2))
                    cv2.fillPoly(barrier_mask, [poly], 255)
                    
    # Morphological dilation/closure to bridge small architectural gaps & door clearances
    kernel = np.ones((gap_closure_kernel_size, gap_closure_kernel_size), np.uint8)
    closed_barriers = cv2.dilate(barrier_mask, kernel)
    
    # Invert to isolate open interior and exterior spaces
    open_spaces = cv2.bitwise_not(closed_barriers)
    
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(open_spaces)
    if num_labels <= 1:
        return []
        
    # Identify exterior boundary spaces (components touching image edges)
    border_labels = set(labels[0, :]).union(labels[-1, :]).union(labels[:, 0]).union(labels[:, -1])
    
    # Also mark any massive space (> 40% of image) as exterior background
    total_pixels = float(image_width * image_height)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] > 0.40 * total_pixels:
            border_labels.add(i)
            
    rooms: List[Dict[str, Any]] = []
    
    for label_idx in range(1, num_labels):
        if label_idx in border_labels:
            continue
            
        area = float(stats[label_idx, cv2.CC_STAT_AREA])
        if area < min_room_area or area > max_room_area:
            continue
            
        # Extract binary mask for the specific room component
        room_mask = (labels == label_idx).astype(np.uint8) * 255
        
        # Smooth and find external contour
        contours, _ = cv2.findContours(room_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue
            
        cnt = max(contours, key=cv2.contourArea)
        cnt_area = float(cv2.contourArea(cnt))
        if cnt_area < min_room_area:
            continue
            
        # Simplify polygon vertices using Douglas-Peucker algorithm
        approx = cv2.approxPolyDP(cnt, epsilon=polygon_simplification_epsilon, closed=True)
        if len(approx) < 4:
            continue
            
        x, y, w, h = cv2.boundingRect(approx)
        if w < 20 or h < 20:
            continue
            
        # Flatten polygon points into COCO format: [x1, y1, x2, y2, ...]
        flat_poly = approx.flatten().astype(float).round(3).tolist()
        
        room_ann = {
            "category_id": 4,  # Standardized room class ID
            "bbox": [round(float(x), 3), round(float(y), 3), round(float(w), 3), round(float(h), 3)],
            "segmentation": [flat_poly],
            "area": round(cnt_area, 3),
            "iscrowd": 0,
            "room_type": "enclosed_room"
        }
        rooms.append(room_ann)
        
    return rooms

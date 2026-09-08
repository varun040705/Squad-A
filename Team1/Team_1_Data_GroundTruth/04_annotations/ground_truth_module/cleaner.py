"""
Dataset Cleaner and Normalizer for Task T1.2 Ground-Truth Annotations.
Standardizes category IDs, strips noise classes, and validates geometries.
"""

from typing import Dict, List, Tuple, Any

STANDARD_CATEGORIES = [
    {"id": 1, "name": "wall", "supercategory": "architectural"},
    {"id": 2, "name": "door", "supercategory": "architectural"},
    {"id": 3, "name": "window", "supercategory": "architectural"},
    {"id": 4, "name": "room", "supercategory": "space"},
    {"id": 5, "name": "dimension", "supercategory": "annotation"},
]

RAW_CATEGORY_NAME_MAP = {
    "wall": 1,
    "door": 2,
    "window": 3,
}

IGNORE_CATEGORY_NAMES = {"-_-", "background", "floor-plan", "none"}


def clean_coco_dataset(
    coco_data: Dict[str, Any],
    default_width: int = 1920,
    default_height: int = 1080
) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """
    Cleans raw COCO annotations by removing noise categories,
    re-mapping standard architectural IDs, and validating geometric boundaries.
    """
    raw_cats = {c["id"]: c["name"].lower().strip() for c in coco_data.get("categories", [])}
    
    images = coco_data.get("images", [])
    raw_annotations = coco_data.get("annotations", [])
    
    img_dimensions = {
        img["id"]: (img.get("width", default_width), img.get("height", default_height))
        for img in images
    }
    
    cleaned_annotations = []
    stats = {
        "retained_walls": 0,
        "retained_doors": 0,
        "retained_windows": 0,
        "dropped_noise": 0,
        "clipped_polygons": 0,
    }
    
    new_ann_id = 1
    for ann in raw_annotations:
        cat_name = raw_cats.get(ann.get("category_id"), "")
        if cat_name in IGNORE_CATEGORY_NAMES or not cat_name:
            stats["dropped_noise"] += 1
            continue
            
        new_cat_id = RAW_CATEGORY_NAME_MAP.get(cat_name)
        if not new_cat_id:
            stats["dropped_noise"] += 1
            continue
            
        img_w, img_h = img_dimensions.get(ann["image_id"], (default_width, default_height))
        
        # Validate bbox [x, y, w, h]
        bbox = ann.get("bbox", [0, 0, 0, 0])
        if len(bbox) != 4:
            continue
        x, y, w, h = bbox
        if w <= 0 or h <= 0:
            continue
            
        # Clamp bbox to image boundaries
        clamped_x = max(0.0, min(float(x), float(img_w)))
        clamped_y = max(0.0, min(float(y), float(img_h)))
        clamped_w = min(float(w), float(img_w) - clamped_x)
        clamped_h = min(float(h), float(img_h) - clamped_y)
        if clamped_w <= 0 or clamped_h <= 0:
            continue
            
        # Validate & clamp polygon segmentation
        valid_segments = []
        for seg in ann.get("segmentation", []):
            if len(seg) < 6:
                continue
            clamped_seg = []
            for i in range(0, len(seg), 2):
                px = max(0.0, min(float(seg[i]), float(img_w)))
                py = max(0.0, min(float(seg[i + 1]), float(img_h))) if i + 1 < len(seg) else 0.0
                clamped_seg.extend([round(px, 3), round(py, 3)])
            valid_segments.append(clamped_seg)
            
        if not valid_segments:
            # Fallback to bbox polygon
            valid_segments = [[
                round(clamped_x, 3), round(clamped_y, 3),
                round(clamped_x + clamped_w, 3), round(clamped_y, 3),
                round(clamped_x + clamped_w, 3), round(clamped_y + clamped_h, 3),
                round(clamped_x, 3), round(clamped_y + clamped_h, 3)
            ]]
            
        area = ann.get("area")
        if not area or area <= 0:
            area = clamped_w * clamped_h
            
        cleaned_ann = {
            "id": new_ann_id,
            "image_id": ann["image_id"],
            "category_id": new_cat_id,
            "bbox": [round(clamped_x, 3), round(clamped_y, 3), round(clamped_w, 3), round(clamped_h, 3)],
            "segmentation": valid_segments,
            "area": round(float(area), 3),
            "iscrowd": 0
        }
        cleaned_annotations.append(cleaned_ann)
        new_ann_id += 1
        
        if new_cat_id == 1:
            stats["retained_walls"] += 1
        elif new_cat_id == 2:
            stats["retained_doors"] += 1
        elif new_cat_id == 3:
            stats["retained_windows"] += 1
            
    cleaned_dataset = {
        "info": {
            "year": 2026,
            "version": "1.0",
            "description": "Squad-A Ground-Truth Cleaned Dataset (T1.2)",
            "contributor": "Team 1 - Member 2 (Ground-Truth Annotation)"
        },
        "licenses": coco_data.get("licenses", []),
        "categories": STANDARD_CATEGORIES,
        "images": images,
        "annotations": cleaned_annotations
    }
    
    return cleaned_dataset, stats

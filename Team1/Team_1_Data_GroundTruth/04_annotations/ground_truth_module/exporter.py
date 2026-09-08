"""
Schema Alignment & Exporter Helper for Task T1.2 -> T1.3.
Exports ground-truth annotations into a hierarchical, developer-friendly ground_truth.json
ready for Member 3's schema alignment and Member 4's evaluation harness.
"""

import os
import json
from typing import Dict, Any, List


def export_intermediate_ground_truth(
    coco_json_path: str,
    output_path: str = "ground_truth/ground_truth.json",
    split_name: str = "test"
) -> str:
    """
    Converts COCO flat ground-truth annotations into an image-centric intermediate schema.
    Structure per image:
    {
        "image_id": int,
        "file_name": str,
        "dimensions_wh": [width, height],
        "walls": [{"bbox": [...], "polygon": [...], "area": float}],
        "doors": [...],
        "windows": [...],
        "rooms": [...],
        "dimensions": [...]
    }
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(coco_json_path, "r", encoding="utf-8") as f:
        coco = json.load(f)

    cat_map = {c["id"]: c["name"] for c in coco.get("categories", [])}

    # Group annotations by image_id
    grouped_anns: Dict[int, Dict[str, List[Dict[str, Any]]]] = {}
    for ann in coco.get("annotations", []):
        img_id = ann["image_id"]
        if img_id not in grouped_anns:
            grouped_anns[img_id] = {
                "walls": [],
                "doors": [],
                "windows": [],
                "rooms": [],
                "dimensions": []
            }
        cat_name = cat_map.get(ann["category_id"], "other")
        target_key = cat_name + "s" if not cat_name.endswith("s") else cat_name
        if target_key not in grouped_anns[img_id]:
            grouped_anns[img_id][target_key] = []

        item = {
            "id": ann["id"],
            "bbox": ann.get("bbox"),
            "segmentation": ann.get("segmentation"),
            "area": ann.get("area")
        }
        if "room_type" in ann:
            item["room_type"] = ann["room_type"]
        if "dimension_type" in ann:
            item["dimension_type"] = ann["dimension_type"]

        grouped_anns[img_id][target_key].append(item)

    export_records = []
    for img in coco.get("images", []):
        img_id = img["id"]
        anns = grouped_anns.get(img_id, {
            "walls": [], "doors": [], "windows": [], "rooms": [], "dimensions": []
        })
        export_records.append({
            "image_id": img_id,
            "file_name": img.get("file_name"),
            "width": img.get("width"),
            "height": img.get("height"),
            "elements": {
                "walls": anns.get("walls", []),
                "doors": anns.get("doors", []),
                "windows": anns.get("windows", []),
                "rooms": anns.get("rooms", []),
                "dimensions": anns.get("dimensions", [])
            },
            "summary_counts": {
                "walls_count": len(anns.get("walls", [])),
                "doors_count": len(anns.get("doors", [])),
                "windows_count": len(anns.get("windows", [])),
                "rooms_count": len(anns.get("rooms", [])),
                "dimensions_count": len(anns.get("dimensions", []))
            }
        })

    payload = {
        "dataset": "Squad-A Floor Plan Ground Truth",
        "task": "T1.2 Ground-Truth Annotation",
        "split": split_name,
        "total_images": len(export_records),
        "target_classes": ["walls", "doors", "windows", "rooms", "dimensions"],
        "plans": export_records
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return output_path

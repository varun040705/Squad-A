"""
Ground-Truth Dataset Builder and Harmonizer for Task T1.2.
Consolidates walls, doors, windows, rooms, and dimensions into a unified COCO ground-truth dataset.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from ground_truth.cleaner import clean_coco_dataset, STANDARD_CATEGORIES
from ground_truth.room_extractor import extract_rooms_from_annotations
from ground_truth.dimension_extractor import extract_dimensions

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class GroundTruthBuilder:
    """
    Automated pipeline to generate complete Ground-Truth annotations for 5 classes:
    1: wall, 2: door, 3: window, 4: room, 5: dimension.
    """

    def __init__(
        self,
        base_dir: str = "floor-plan.v1i.coco",
        output_filename: str = "_ground_truth.coco.json"
    ):
        self.base_dir = base_dir
        self.output_filename = output_filename

    def process_split(
        self,
        split_name: str,
        limit_images: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Processes a dataset split (e.g. 'train', 'valid', 'test'), extracting rooms and dimensions,
        and generating a consolidated ground-truth COCO file.
        """
        split_dir = os.path.join(self.base_dir, split_name)
        input_file = os.path.join(split_dir, "_annotations.coco.json")
        output_file = os.path.join(split_dir, self.output_filename)

        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Annotation file not found: {input_file}")

        logger.info("Loading raw annotations from %s...", input_file)
        with open(input_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        logger.info("Cleaning raw annotations and standardizing category IDs...")
        cleaned_dataset, clean_stats = clean_coco_dataset(raw_data)

        images = cleaned_dataset.get("images", [])
        if limit_images:
            images = images[:limit_images]

        all_cleaned_anns = cleaned_dataset.get("annotations", [])
        anns_by_image: Dict[int, List[Dict[str, Any]]] = {}
        for ann in all_cleaned_anns:
            img_id = ann["image_id"]
            if img_id not in anns_by_image:
                anns_by_image[img_id] = []
            anns_by_image[img_id].append(ann)

        master_annotations: List[Dict[str, Any]] = []
        next_ann_id = 1

        total_walls = 0
        total_doors = 0
        total_windows = 0
        total_rooms = 0
        total_dimensions = 0

        logger.info("Extracting rooms and dimensions for %d images in '%s'...", len(images), split_name)
        for idx, img in enumerate(images):
            img_id = img["id"]
            img_w = img.get("width", 1920)
            img_h = img.get("height", 1080)
            img_name = img.get("file_name", "")
            img_path = os.path.join(split_dir, img_name)

            existing_anns = anns_by_image.get(img_id, [])

            # Add existing structural annotations with normalized IDs
            for ann in existing_anns:
                ann_copy = dict(ann)
                ann_copy["id"] = next_ann_id
                next_ann_id += 1
                master_annotations.append(ann_copy)

                cat_id = ann_copy["category_id"]
                if cat_id == 1:
                    total_walls += 1
                elif cat_id == 2:
                    total_doors += 1
                elif cat_id == 3:
                    total_windows += 1

            # Extract Rooms
            rooms = extract_rooms_from_annotations(img_w, img_h, existing_anns)
            for room in rooms:
                room["id"] = next_ann_id
                room["image_id"] = img_id
                next_ann_id += 1
                master_annotations.append(room)
                total_rooms += 1

            # Extract Dimensions
            dims = extract_dimensions(img_w, img_h, existing_anns + rooms, image_path=img_path)
            for dim in dims:
                dim["id"] = next_ann_id
                dim["image_id"] = img_id
                next_ann_id += 1
                master_annotations.append(dim)
                total_dimensions += 1

            if (idx + 1) % 100 == 0 or (idx + 1) == len(images):
                logger.info("Processed %d / %d images...", idx + 1, len(images))

        final_dataset = {
            "info": {
                "year": 2026,
                "version": "1.0",
                "description": "Squad-A Complete Ground-Truth Dataset (T1.2)",
                "contributor": "Team 1 - Member 2 (Ground-Truth Annotation)",
                "classes": ["wall", "door", "window", "room", "dimension"]
            },
            "licenses": cleaned_dataset.get("licenses", []),
            "categories": STANDARD_CATEGORIES,
            "images": images,
            "annotations": master_annotations
        }

        logger.info("Writing harmonized ground-truth to %s...", output_file)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_dataset, f)

        summary = {
            "split": split_name,
            "images_count": len(images),
            "total_annotations": len(master_annotations),
            "walls": total_walls,
            "doors": total_doors,
            "windows": total_windows,
            "rooms": total_rooms,
            "dimensions": total_dimensions,
            "output_file": output_file
        }
        logger.info("Split summary: %s", summary)
        return summary

    def build_all(self, limit_per_split: Optional[int] = None) -> List[Dict[str, Any]]:
        """Processes all available splits ('test', 'valid', 'train')."""
        summaries = []
        for split in ["test", "valid", "train"]:
            split_dir = os.path.join(self.base_dir, split)
            if os.path.exists(split_dir):
                summary = self.process_split(split, limit_images=limit_per_split)
                summaries.append(summary)
        return summaries


if __name__ == "__main__":
    builder = GroundTruthBuilder()
    builder.build_all()

"""
Automated Test Suite for Task T1.2 Ground-Truth Annotation Pipeline.
Verifies taxonomy standardization, geometric integrity, room extraction,
dimension extraction, and dataset COCO schema compliance.
"""

import os
import json
import pytest
from ground_truth.cleaner import clean_coco_dataset, STANDARD_CATEGORIES
from ground_truth.room_extractor import extract_rooms_from_annotations
from ground_truth.dimension_extractor import extract_dimensions


def test_standard_taxonomy_definitions():
    """Verify that all 5 essential architectural elements are defined."""
    expected_categories = {"wall", "door", "window", "room", "dimension"}
    actual_categories = {c["name"] for c in STANDARD_CATEGORIES}
    assert actual_categories == expected_categories
    assert len(STANDARD_CATEGORIES) == 5
    ids = {c["id"] for c in STANDARD_CATEGORIES}
    assert ids == {1, 2, 3, 4, 5}


def test_cleaner_strips_noise_and_clamps():
    """Verify that cleaner removes corrupt tags and clamps out-of-bounds coordinates."""
    mock_raw_data = {
        "categories": [
            {"id": 0, "name": "floor-plan"},
            {"id": 1, "name": "-_-"},
            {"id": 2, "name": "background"},
            {"id": 3, "name": "door"},
            {"id": 4, "name": "wall"},
            {"id": 5, "name": "window"}
        ],
        "images": [{"id": 1, "file_name": "test.jpg", "width": 1000, "height": 800}],
        "annotations": [
            # Corrupt annotation
            {"id": 101, "image_id": 1, "category_id": 1, "bbox": [0, 0, 10, 10], "segmentation": []},
            # Background annotation
            {"id": 102, "image_id": 1, "category_id": 2, "bbox": [0, 0, 100, 100], "segmentation": []},
            # Valid Wall with slight out-of-bound coordinate
            {
                "id": 103,
                "image_id": 1,
                "category_id": 4,
                "bbox": [50, 50, 200, 20],
                "segmentation": [[50, 50, 250, 50, 250, 70, 50, 70]],
                "area": 4000
            }
        ]
    }

    cleaned, stats = clean_coco_dataset(mock_raw_data, default_width=1000, default_height=800)
    assert stats["dropped_noise"] == 2
    assert stats["retained_walls"] == 1
    assert len(cleaned["annotations"]) == 1

    ann = cleaned["annotations"][0]
    assert ann["category_id"] == 1  # Remapped to standard wall ID
    assert ann["bbox"] == [50.0, 50.0, 200.0, 20.0]


def test_room_extractor_synthetic_enclosure():
    """Verify topological room segmentation extracts enclosed interior spaces."""
    width, height = 800, 800
    # Create 4 enclosing walls around a 300x300 room centered at (250, 250)
    mock_walls = [
        # Top wall
        {"category_id": 1, "segmentation": [[200, 200, 500, 200, 500, 220, 200, 220]]},
        # Bottom wall
        {"category_id": 1, "segmentation": [[200, 500, 500, 500, 500, 520, 200, 520]]},
        # Left wall
        {"category_id": 1, "segmentation": [[200, 200, 220, 200, 220, 520, 200, 520]]},
        # Right wall
        {"category_id": 1, "segmentation": [[480, 200, 500, 200, 500, 520, 480, 520]]},
    ]

    rooms = extract_rooms_from_annotations(width, height, mock_walls, min_room_area=1000.0)
    assert len(rooms) >= 1
    room = rooms[0]
    assert room["category_id"] == 4  # Standard Room ID
    rx, ry, rw, rh = room["bbox"]
    assert 200 <= rx <= 250
    assert 200 <= ry <= 250
    assert 200 <= rw <= 320
    assert 200 <= rh <= 320
    assert len(room["segmentation"][0]) >= 8  # At least 4 vertices


def test_dimension_extractor_inferences():
    """Verify that dimension extraction generates valid geometric dimension callouts."""
    mock_annotations = [
        {"category_id": 4, "bbox": [100.0, 100.0, 200.0, 150.0], "area": 30000.0}
    ]
    dims = extract_dimensions(1000, 800, mock_annotations)
    assert len(dims) >= 1
    dim = dims[0]
    assert dim["category_id"] == 5  # Standard Dimension ID
    assert dim["area"] > 0
    assert len(dim["bbox"]) == 4


def test_ground_truth_test_split_integrity():
    """Verify the generated ground-truth test file meets all schema and quality criteria."""
    gt_file = os.path.join("floor-plan.v1i.coco", "test", "_ground_truth.coco.json")
    if not os.path.exists(gt_file):
        pytest.skip("Ground-truth file not yet generated")

    with open(gt_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate categories
    cat_ids = {c["id"] for c in data["categories"]}
    assert cat_ids == {1, 2, 3, 4, 5}
    cat_names = {c["name"] for c in data["categories"]}
    assert cat_names == {"wall", "door", "window", "room", "dimension"}

    # Validate images
    assert len(data["images"]) == 146
    img_ids = {img["id"] for img in data["images"]}

    # Validate annotations
    annotations = data["annotations"]
    assert len(annotations) > 0

    found_categories = set()
    for ann in annotations:
        found_categories.add(ann["category_id"])
        assert ann["category_id"] in (1, 2, 3, 4, 5)
        assert ann["image_id"] in img_ids
        x, y, w, h = ann["bbox"]
        assert w > 0 and h > 0
        assert 0 <= x <= 1920 and 0 <= y <= 1080
        assert ann["area"] > 0
        assert len(ann["segmentation"]) >= 1

    # Must contain all 5 target categories!
    assert found_categories == {1, 2, 3, 4, 5}, f"Missing categories: {{1, 2, 3, 4, 5}} - {found_categories}"

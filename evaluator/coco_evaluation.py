import glob
import json
from pathlib import Path

from evaluator.coco_adapter import (
    load_coco,
    convert_coco_image,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

COCO_FILE = (
    PROJECT_ROOT
    / "floor_plan_dataset"
    / "test"
    / "_annotations.coco.json"
)

GROUND_TRUTH_DIR = (
    PROJECT_ROOT
    / "real_data"
    / "ground_truth"
)


def get_test_dataset():
    annotation_files = glob.glob(
        "floor_plan_dataset/test/*.json"
    )

    if not annotation_files:
        raise FileNotFoundError(
            "No COCO annotation file found."
        )

    return annotation_files[0]


def get_image_ids(coco_data):
    return [
        image["id"]
        for image in coco_data["images"]
    ]


def load_test_dataset():
    annotation_file = get_test_dataset()

    coco_data = load_coco(
        annotation_file
    )

    image_ids = get_image_ids(
        coco_data
    )

    return coco_data, image_ids


def convert_all_test_images(
    coco_data,
    image_ids
):
    results = []

    for image_id in image_ids:

        result = convert_coco_image(
            coco_data,
            image_id
        )

        results.append(result)

    return results


def save_ground_truth_files(
    coco_data,
    image_ids
):
    GROUND_TRUTH_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    for image_id in image_ids:

        result = convert_coco_image(
            coco_data,
            image_id
        )

        output_file = (
            GROUND_TRUTH_DIR
            / f"{image_id}.json"
        )

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                result,
                file,
                indent=2
            )

    print(
        f"Created {len(image_ids)} "
        f"ground-truth files."
    )


if __name__ == "__main__":

    coco_data, image_ids = load_test_dataset()

    save_ground_truth_files(
        coco_data,
        image_ids
    )
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

OUTPUT_DIR = (
    PROJECT_ROOT
    / "real_data"
    / "predictions"
)


def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    coco_data = load_coco(COCO_FILE)

    for image in coco_data["images"]:

        image_id = image["id"]

        result = convert_coco_image(
            coco_data,
            image_id
        )

        output_file = (
            OUTPUT_DIR
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
        f"Created {len(coco_data['images'])} "
        f"prediction-format files."
    )


if __name__ == "__main__":
    main()
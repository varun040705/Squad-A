import json


CATEGORY_MAP = {
    3: "doors",
    4: "walls",
    5: "windows",
}


def load_coco(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def bbox_to_centerline(bbox):
    x, y, width, height = bbox

    if width >= height:
        return [
            [x, y + height / 2],
            [x + width, y + height / 2]
        ]

    return [
        [x + width / 2, y],
        [x + width / 2, y + height]
    ]


def bbox_to_position(bbox):
    x, y, width, height = bbox

    return [
        x + width / 2,
        y + height / 2
    ]


def segmentation_to_polygon(segmentation):
    if not segmentation:
        return []

    points = segmentation[0]

    return [
        [points[i], points[i + 1]]
        for i in range(0, len(points), 2)
    ]


def convert_coco_image(coco_data, image_id):
    annotations = [
        annotation
        for annotation in coco_data["annotations"]
        if annotation["image_id"] == image_id
    ]

    walls = []
    doors = []
    windows = []

    for annotation in annotations:

        category = CATEGORY_MAP.get(
            annotation["category_id"]
        )

        if category == "walls":
            walls.append({
                "id": str(annotation["id"]),
                "centerline": bbox_to_centerline(
                    annotation["bbox"]
                ),
                "thickness_mm": 0,
                "confidence": 1.0,
                "openings": [],
                "connected_walls": []
            })

        elif category == "doors":
            doors.append({
                "id": str(annotation["id"]),
                "position": bbox_to_position(
                    annotation["bbox"]
                ),
                "width_mm": annotation["bbox"][2]
            })

        elif category == "windows":
            windows.append({
                "id": str(annotation["id"]),
                "position": bbox_to_position(
                    annotation["bbox"]
                ),
                "width_mm": annotation["bbox"][2]
            })

    return {
        "project": {
            "levels": [
                {
                    "id": "level_1",
                    "elevation_mm": 0,
                    "height_mm": 3000,
                    "walls": walls,
                    "doors": doors,
                    "windows": windows,
                    "rooms": [],
                    "columns": [],
                    "stairs": []
                }
            ],
            "scale": {
                "mm_per_pixel": 1.0,
                "method": "not_available",
                "confidence": 0.0
            },
            "metadata": {
                "source_image": str(image_id),
                "units": "mm"
            }
        }
    }
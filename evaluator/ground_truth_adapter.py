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

    if isinstance(segmentation, list):
        points = segmentation[0] if isinstance(
            segmentation[0],
            list
        ) else segmentation

        return [
            [points[i], points[i + 1]]
            for i in range(0, len(points), 2)
        ]

    return []


def convert_t1_2_ground_truth(data):
    plans = data.get("plans", [])

    levels = []

    for index, plan in enumerate(plans):

        elements = plan.get("elements", {})

        walls = []
        doors = []
        windows = []
        rooms = []

        for wall in elements.get("walls", []):
            bbox = wall.get("bbox")

            if bbox:
                walls.append({
                    "id": str(wall.get("id")),
                    "centerline": bbox_to_centerline(bbox),
                    "thickness_mm": 0,
                    "confidence": 1.0,
                    "openings": [],
                    "connected_walls": []
                })

        for door in elements.get("doors", []):
            bbox = door.get("bbox")

            if bbox:
                doors.append({
                    "id": str(door.get("id")),
                    "position": bbox_to_position(bbox),
                    "width_mm": bbox[2]
                })

        for window in elements.get("windows", []):
            bbox = window.get("bbox")

            if bbox:
                windows.append({
                    "id": str(window.get("id")),
                    "position": bbox_to_position(bbox),
                    "width_mm": bbox[2]
                })

        for room in elements.get("rooms", []):
            polygon = segmentation_to_polygon(
                room.get("segmentation")
            )

            if polygon:
                rooms.append({
                    "id": str(room.get("id")),
                    "polygon": polygon,
                    "label": "Room"
                })

        levels.append({
            "id": f"level_{index + 1}",
            "elevation_mm": 0,
            "height_mm": 3000,
            "walls": walls,
            "doors": doors,
            "windows": windows,
            "rooms": rooms,
            "columns": [],
            "stairs": []
        })

    return {
        "project": {
            "levels": levels,
            "scale": {
                "mm_per_pixel": 1.0,
                "method": "not_available",
                "confidence": 0.0
            },
            "metadata": {
                "source_image": "T1.2_ground_truth",
                "units": "mm"
            }
        }
    }
import math


def point_distance(p1, p2):
    return math.sqrt(
        (p1[0] - p2[0]) ** 2 +
        (p1[1] - p2[1]) ** 2
    )


def line_distance(line1, line2):
    start1, end1 = line1
    start2, end2 = line2

    direct = (
        point_distance(start1, start2) +
        point_distance(end1, end2)
    ) / 2

    reversed_distance = (
        point_distance(start1, end2) +
        point_distance(end1, start2)
    ) / 2

    return min(direct, reversed_distance)


def polygon_distance(polygon1, polygon2):
    if len(polygon1) != len(polygon2):
        return float("inf")

    direct = sum(
        point_distance(p1, p2)
        for p1, p2 in zip(polygon1, polygon2)
    ) / len(polygon1)

    reversed_distance = sum(
        point_distance(p1, p2)
        for p1, p2 in zip(polygon1, reversed(polygon2))
    ) / len(polygon1)

    return min(direct, reversed_distance)


def geometry_distance(geometry1, geometry2):
    if not geometry1 or not geometry2:
        return float("inf")

    # Point geometry: [x, y]
    if (
        isinstance(geometry1[0], (int, float))
        and isinstance(geometry2[0], (int, float))
    ):
        return point_distance(geometry1, geometry2)

    # Line geometry: [[x1, y1], [x2, y2]]
    if len(geometry1) == 2 and len(geometry2) == 2:
        return line_distance(geometry1, geometry2)

    # Polygon geometry
    return polygon_distance(geometry1, geometry2)


def match_elements(
    ground_truth_elements,
    prediction_elements,
    geometry_key="centerline",
    tolerance=10.0
):
    matches = []
    used_predictions = set()

    for gt in ground_truth_elements:
        best_prediction = None
        best_distance = float("inf")
        best_index = None

        for index, prediction in enumerate(prediction_elements):
            if index in used_predictions:
                continue

            if geometry_key not in gt or geometry_key not in prediction:
                continue

            distance = geometry_distance(
                gt[geometry_key],
                prediction[geometry_key]
            )

            if distance <= tolerance and distance < best_distance:
                best_distance = distance
                best_prediction = prediction
                best_index = index

        if best_prediction is not None:
            matches.append({
                "ground_truth_id": gt.get("id"),
                "prediction_id": best_prediction.get("id"),
                "distance": best_distance
            })
            used_predictions.add(best_index)

    true_positives = len(matches)
    false_negatives = len(ground_truth_elements) - true_positives
    false_positives = len(prediction_elements) - true_positives

    return {
        "matches": matches,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives
    }
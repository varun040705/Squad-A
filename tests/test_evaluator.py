import json

from evaluator.validator import validate_schema
from evaluator.matching import match_elements
from evaluator.metrics import calculate_metrics
from evaluator.scale_metrics import calculate_scale_accuracy


def load_sample(filename):
    path = f"sample_data/{filename}"

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def test_ground_truth_schema():
    data = load_sample("ground_truth.json")

    errors = validate_schema(data)

    assert errors == []


def test_prediction_schema():
    data = load_sample("prediction.json")

    errors = validate_schema(data)

    assert errors == []


def test_wall_matching():
    ground_truth = load_sample("ground_truth.json")
    prediction = load_sample("prediction.json")

    gt_walls = ground_truth["project"]["levels"][0]["walls"]
    predicted_walls = prediction["project"]["levels"][0]["walls"]

    result = match_elements(
        gt_walls,
        predicted_walls,
        geometry_key="centerline",
        tolerance=10.0
    )

    assert result["true_positives"] == 3
    assert result["false_positives"] == 1
    assert result["false_negatives"] == 1


def test_door_matching():
    ground_truth = load_sample("ground_truth.json")
    prediction = load_sample("prediction.json")

    gt_doors = ground_truth["project"]["levels"][0]["doors"]
    predicted_doors = prediction["project"]["levels"][0]["doors"]

    result = match_elements(
        gt_doors,
        predicted_doors,
        geometry_key="position",
        tolerance=10.0
    )

    assert result["true_positives"] == 1
    assert result["false_positives"] == 0
    assert result["false_negatives"] == 1


def test_window_matching():
    ground_truth = load_sample("ground_truth.json")
    prediction = load_sample("prediction.json")

    gt_windows = ground_truth["project"]["levels"][0]["windows"]
    predicted_windows = prediction["project"]["levels"][0]["windows"]

    result = match_elements(
        gt_windows,
        predicted_windows,
        geometry_key="position",
        tolerance=10.0
    )

    assert result["true_positives"] == 1
    assert result["false_positives"] == 1
    assert result["false_negatives"] == 1


def test_room_matching():
    ground_truth = load_sample("ground_truth.json")
    prediction = load_sample("prediction.json")

    gt_rooms = ground_truth["project"]["levels"][0]["rooms"]
    predicted_rooms = prediction["project"]["levels"][0]["rooms"]

    result = match_elements(
        gt_rooms,
        predicted_rooms,
        geometry_key="polygon",
        tolerance=10.0
    )

    assert result["true_positives"] == 1
    assert result["false_positives"] == 0
    assert result["false_negatives"] == 1


def test_precision():
    result = {
        "true_positives": 3,
        "false_positives": 1,
        "false_negatives": 1
    }

    metrics = calculate_metrics(result)

    assert metrics["precision"] == 0.75


def test_recall():
    result = {
        "true_positives": 3,
        "false_positives": 1,
        "false_negatives": 1
    }

    metrics = calculate_metrics(result)

    assert metrics["recall"] == 0.75


def test_scale_accuracy():
    result = calculate_scale_accuracy(4.0, 4.2)

    assert result["absolute_error"] == 0.2
    assert result["percentage_error"] == 5.0

def test_scale_zero_error():
    result = calculate_scale_accuracy(4.0, 4.0)

    assert result["absolute_error"] == 0.0
    assert result["percentage_error"] == 0.0


def test_empty_matching():
    result = match_elements(
        [],
        [],
        geometry_key="position",
        tolerance=10.0
    )

    assert result["true_positives"] == 0
    assert result["false_positives"] == 0
    assert result["false_negatives"] == 0


def test_all_predictions_are_false_positives():
    ground_truth = []

    predictions = [
        {
            "id": "pred_001",
            "position": [100, 100]
        },
        {
            "id": "pred_002",
            "position": [200, 200]
        }
    ]

    result = match_elements(
        ground_truth,
        predictions,
        geometry_key="position",
        tolerance=10.0
    )

    assert result["true_positives"] == 0
    assert result["false_positives"] == 2
    assert result["false_negatives"] == 0

from evaluator.report import calculate_overall_element_score


def test_overall_element_f1():
    elements = {
        "walls": {"f1_score": 0.75},
        "doors": {"f1_score": 0.67},
        "windows": {"f1_score": 0.50},
        "rooms": {"f1_score": 0.67}
    }

    score = calculate_overall_element_score(elements)

    assert round(score, 2) == 0.65

from evaluator.ground_truth_adapter import (
    bbox_to_centerline,
    bbox_to_position
)


def test_bbox_to_centerline():
    result = bbox_to_centerline(
        [100, 100, 500, 20]
    )

    assert result == [
        [100, 110.0],
        [600, 110.0]
    ]


def test_bbox_to_position():
    result = bbox_to_position(
        [100, 100, 200, 100]
    )

    assert result == [
        200.0,
        150.0
    ]
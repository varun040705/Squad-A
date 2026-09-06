import json
from pathlib import Path

from evaluator.config import (
    GROUND_TRUTH_DIR,
    PREDICTIONS_DIR,
    REPORTS_DIR,
    WALL_TOLERANCE,
    DOOR_TOLERANCE,
    WINDOW_TOLERANCE,
    ROOM_TOLERANCE,
)
from evaluator.validator import validate_schema
from evaluator.matching import match_elements
from evaluator.metrics import calculate_metrics
from evaluator.scale_metrics import calculate_scale_accuracy
from evaluator.report import (
    build_report,
    build_dataset_report,
    save_report,
    print_report,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SAMPLE_GROUND_TRUTH = (
    PROJECT_ROOT / "sample_data" / "ground_truth.json"
)

SAMPLE_PREDICTION = (
    PROJECT_ROOT / "sample_data" / "prediction.json"
)


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def get_input_files():

    real_ground_truth = sorted(
        GROUND_TRUTH_DIR.glob("*.json")
    )

    real_predictions = sorted(
        PREDICTIONS_DIR.glob("*.json")
    )

    if real_ground_truth and real_predictions:

        prediction_map = {
            file.name: file
            for file in real_predictions
        }

        matched_files = []

        for gt_file in real_ground_truth:

            prediction_file = prediction_map.get(
                gt_file.name
            )

            if prediction_file:
                matched_files.append(
                    (gt_file, prediction_file)
                )

        if matched_files:
            print(
                f"Found {len(matched_files)} "
                f"real-data pair(s)."
            )

            return matched_files

    print("No real-data pairs found.")
    print("Using sample data.")

    return [
        (SAMPLE_GROUND_TRUTH, SAMPLE_PREDICTION)
    ]
def evaluate_element(
    ground_truth_elements,
    prediction_elements,
    geometry_key,
    tolerance
):
    match_result = match_elements(
        ground_truth_elements,
        prediction_elements,
        geometry_key=geometry_key,
        tolerance=tolerance
    )

    return calculate_metrics(match_result)


def evaluate_level(
    ground_truth_level,
    prediction_level
):
    element_metrics = {}

    element_metrics["walls"] = evaluate_element(
        ground_truth_level["walls"],
        prediction_level["walls"],
        "centerline",
        WALL_TOLERANCE
    )

    element_metrics["doors"] = evaluate_element(
        ground_truth_level["doors"],
        prediction_level["doors"],
        "position",
        DOOR_TOLERANCE
    )

    element_metrics["windows"] = evaluate_element(
        ground_truth_level["windows"],
        prediction_level["windows"],
        "position",
        WINDOW_TOLERANCE
    )

    element_metrics["rooms"] = evaluate_element(
        ground_truth_level["rooms"],
        prediction_level["rooms"],
        "polygon",
        ROOM_TOLERANCE
    )

    return element_metrics


def evaluate_plan(
    ground_truth_file,
    prediction_file
):
    ground_truth = load_json(
        ground_truth_file
    )

    prediction = load_json(
        prediction_file
    )

    gt_errors = validate_schema(
        ground_truth
    )

    if gt_errors:
        print(
            "Ground Truth validation failed:"
        )

        for error in gt_errors:
            print(f"  - {error}")

        return None

    pred_errors = validate_schema(
        prediction
    )

    if pred_errors:
        print(
            "Prediction validation failed:"
        )

        for error in pred_errors:
            print(f"  - {error}")

        return None

    gt_levels = ground_truth["project"]["levels"]
    pred_levels = prediction["project"]["levels"]

    level_count = min(
        len(gt_levels),
        len(pred_levels)
    )

    if len(gt_levels) != len(pred_levels):
        print(
            f"Warning: Ground Truth has "
            f"{len(gt_levels)} level(s), "
            f"Prediction has "
            f"{len(pred_levels)} level(s)."
        )

    combined_elements = {}

    for element_type in [
        "walls",
        "doors",
        "windows",
        "rooms"
    ]:
        combined_elements[element_type] = {
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0
        }

    level_reports = []

    for index in range(level_count):

        level_metrics = evaluate_level(
            gt_levels[index],
            pred_levels[index]
        )

        level_reports.append({
            "level_id": gt_levels[index].get(
                "id",
                f"level_{index + 1}"
            ),
            "elements": level_metrics
        })

        for element_type, metrics in level_metrics.items():

            combined_elements[element_type][
                "true_positives"
            ] += metrics["true_positives"]

            combined_elements[element_type][
                "false_positives"
            ] += metrics["false_positives"]

            combined_elements[element_type][
                "false_negatives"
            ] += metrics["false_negatives"]

    for element_type, metrics in combined_elements.items():

        combined_elements[element_type] = calculate_metrics(
            metrics
        )

    scale_metrics = calculate_scale_accuracy(
        ground_truth["project"]["scale"][
            "mm_per_pixel"
        ],
        prediction["project"]["scale"][
            "mm_per_pixel"
        ]
    )

    return build_report(
        combined_elements,
        scale_metrics,
        level_reports
    )


def main():

    input_files = get_input_files()

    if not input_files:
        return

    plan_reports = []

    for ground_truth_file, prediction_file in input_files:

        print("\n================================")
        print(
            f"Ground Truth : {ground_truth_file}"
        )
        print(
            f"Prediction   : {prediction_file}"
        )
        print("================================")

        report = evaluate_plan(
            ground_truth_file,
            prediction_file
        )

        if report is None:
            continue

        plan_reports.append(report)

        print_report(report)

        report_file = (
            REPORTS_DIR /
            f"{Path(ground_truth_file).stem}"
            f"_evaluation.json"
        )

        save_report(
            report,
            report_file
        )

        print(
            f"\nReport saved to: "
            f"{report_file}"
        )

    if plan_reports:

        dataset_report = build_dataset_report(
            plan_reports
        )

        dataset_report_file = (
            REPORTS_DIR /
            "dataset_evaluation_report.json"
        )

        save_report(
            dataset_report,
            dataset_report_file
        )

        print("\n\nDATASET SUMMARY")
        print("================")

        print_report(
            dataset_report
        )

        print(
            f"\nDataset report saved to: "
            f"{dataset_report_file}"
        )


if __name__ == "__main__":
    main()
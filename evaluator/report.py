import json
from pathlib import Path


def calculate_f1(precision, recall):
    if precision + recall == 0:
        return 0.0

    return (
        2 * precision * recall
    ) / (
        precision + recall
    )


def calculate_overall_element_score(elements):
    valid_scores = [
        metrics["f1_score"]
        for metrics in elements.values()
        if metrics.get("available", True)
    ]

    if not valid_scores:
        return 0.0

    return sum(valid_scores) / len(valid_scores)


def build_report(
    element_metrics,
    scale_metrics,
    level_reports=None
):
    report = {
        "elements": element_metrics,
        "scale": scale_metrics,
        "overall_element_f1": calculate_overall_element_score(
            element_metrics
        ),
        "evaluation_status": "integration_test_only",
        "prediction_source": "synthetic_ground_truth_adapter",
        "note": (
            "Predictions were generated from COCO ground truth "
            "for pipeline integration testing. These are not "
            "model accuracy results."
        )
    }

    if level_reports is not None:
        report["levels"] = level_reports

    return report


def build_dataset_report(plan_reports):

    if not plan_reports:
        return {
            "plans_evaluated": 0,
            "elements": {},
            "scale": {
                "status": "unavailable"
            },
            "overall_element_f1": 0.0,
            "evaluation_status": "no_data"
        }

    element_types = [
        "walls",
        "doors",
        "windows",
        "rooms"
    ]

    combined_elements = {}

    for element_type in element_types:

        total_tp = sum(
            report["elements"][element_type]["true_positives"]
            for report in plan_reports
        )

        total_fp = sum(
            report["elements"][element_type]["false_positives"]
            for report in plan_reports
        )

        total_fn = sum(
            report["elements"][element_type]["false_negatives"]
            for report in plan_reports
        )

        available = (
            total_tp + total_fp + total_fn > 0
        )

        if not available:
            combined_elements[element_type] = {
                "available": False,
                "status": "unavailable",
                "reason": "No ground-truth annotations available."
            }
            continue

        precision = (
            total_tp / (total_tp + total_fp)
            if total_tp + total_fp > 0
            else 0.0
        )

        recall = (
            total_tp / (total_tp + total_fn)
            if total_tp + total_fn > 0
            else 0.0
        )

        f1_score = calculate_f1(
            precision,
            recall
        )

        combined_elements[element_type] = {
            "available": True,
            "true_positives": total_tp,
            "false_positives": total_fp,
            "false_negatives": total_fn,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score
        }

    return {
        "plans_evaluated": len(plan_reports),
        "elements": combined_elements,
        "scale": {
            "status": "unavailable",
            "reason": (
                "COCO dataset does not provide actual "
                "mm_per_pixel ground-truth scale."
            )
        },
        "overall_element_f1": calculate_overall_element_score(
            combined_elements
        ),
        "evaluation_status": "integration_test_only",
        "prediction_source": "synthetic_ground_truth_adapter",
        "note": (
            "The prediction files were generated from the "
            "same COCO annotations. Therefore the resulting "
            "Precision/Recall/F1 values are integration-test "
            "values and must not be reported as model accuracy."
        )
    }


def save_report(report, output_path):
    Path(output_path).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            report,
            file,
            indent=2
        )


def print_report(report):

    print("\nEVALUATION REPORT")
    print("=================")

    if "evaluation_status" in report:
        print(
            f"\nStatus : "
            f"{report['evaluation_status']}"
        )

    if "plans_evaluated" in report:
        print(
            f"Plans Evaluated : "
            f"{report['plans_evaluated']}"
        )

    for element, metrics in report["elements"].items():

        print(f"\n{element.title()}")

        if not metrics.get("available", True):
            print("  Status : Unavailable")
            continue

        print(
            f"  Precision : "
            f"{metrics['precision']:.2f}"
        )

        print(
            f"  Recall    : "
            f"{metrics['recall']:.2f}"
        )

        print(
            f"  F1-score  : "
            f"{metrics['f1_score']:.2f}"
        )

    print(
        f"\nOverall Element F1 : "
        f"{report['overall_element_f1']:.2f}"
    )

    scale = report["scale"]

    print("\nScale")

    if scale.get("status") == "unavailable":
        print("  Status : Unavailable")
    else:
        print(
            f"  Ground Truth : "
            f"{scale['ground_truth_mm_per_pixel']:.2f} "
            f"mm/pixel"
        )

        print(
            f"  Prediction   : "
            f"{scale['prediction_mm_per_pixel']:.2f} "
            f"mm/pixel"
        )

        print(
            f"  Error        : "
            f"{scale['percentage_error']:.2f}%"
        )

    if "note" in report:
        print(
            f"\nNOTE: {report['note']}"
        )
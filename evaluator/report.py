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
    if not elements:
        return 0.0

    f1_scores = [
        metrics["f1_score"]
        for metrics in elements.values()
    ]

    return sum(f1_scores) / len(f1_scores)


def build_report(element_metrics, scale_metrics, level_reports=None):
    report = {
        "elements": element_metrics,
        "scale": scale_metrics,
        "overall_element_f1": calculate_overall_element_score(
            element_metrics
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
            "scale": {},
            "overall_element_f1": 0.0
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
            "true_positives": total_tp,
            "false_positives": total_fp,
            "false_negatives": total_fn,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score
        }

    scale_errors = [
        report["scale"]["percentage_error"]
        for report in plan_reports
    ]

    average_scale_error = (
        sum(scale_errors) / len(scale_errors)
    )

    overall_element_f1 = calculate_overall_element_score(
        combined_elements
    )

    return {
        "plans_evaluated": len(plan_reports),
        "elements": combined_elements,
        "scale": {
            "average_percentage_error": average_scale_error
        },
        "overall_element_f1": overall_element_f1
    }


def save_report(report, output_path):
    Path(output_path).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)


def print_report(report):
    print("\nEVALUATION REPORT")
    print("=================")

    if "plans_evaluated" in report:
        print(
            f"\nPlans Evaluated : "
            f"{report['plans_evaluated']}"
        )

    if "levels" in report:
        print(
            f"\nLevels Evaluated : "
            f"{len(report['levels'])}"
        )

        for level_report in report["levels"]:
            print(
                f"\nLevel: "
                f"{level_report['level_id']}"
            )

            for element, metrics in level_report[
                "elements"
            ].items():

                print(
                    f"  {element.title():<8} "
                    f"Precision: "
                    f"{metrics['precision']:.2f}  "
                    f"Recall: "
                    f"{metrics['recall']:.2f}  "
                    f"F1: "
                    f"{metrics['f1_score']:.2f}"
                )

    for element, metrics in report["elements"].items():

        print(f"\n{element.title()}")

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

    if "overall_element_f1" in report:
        print(
            f"\nOverall Element F1 : "
            f"{report['overall_element_f1']:.2f}"
        )

    scale = report["scale"]

    if "ground_truth_mm_per_pixel" in scale:

        print("\nScale")

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

    elif "average_percentage_error" in scale:

        print("\nScale")

        print(
            f"  Average Error : "
            f"{scale['average_percentage_error']:.2f}%"
        )
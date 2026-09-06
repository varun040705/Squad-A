def calculate_precision(true_positives, false_positives):
    total_predictions = true_positives + false_positives

    if total_predictions == 0:
        return 0.0

    return true_positives / total_predictions


def calculate_recall(true_positives, false_negatives):
    total_ground_truth = true_positives + false_negatives

    if total_ground_truth == 0:
        return 0.0

    return true_positives / total_ground_truth


def calculate_f1(precision, recall):
    if precision + recall == 0:
        return 0.0

    return (
        2 * precision * recall
    ) / (
        precision + recall
    )


def calculate_metrics(match_result):
    true_positives = match_result["true_positives"]
    false_positives = match_result["false_positives"]
    false_negatives = match_result["false_negatives"]

    precision = calculate_precision(
        true_positives,
        false_positives
    )

    recall = calculate_recall(
        true_positives,
        false_negatives
    )

    f1_score = calculate_f1(
        precision,
        recall
    )

    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score
    }
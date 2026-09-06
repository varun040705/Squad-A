def calculate_scale_accuracy(ground_truth_scale, prediction_scale):
    absolute_error = round(
        abs(prediction_scale - ground_truth_scale),
        10
    )

    percentage_error = round(
        (absolute_error / ground_truth_scale) * 100,
        10
    )

    return {
        "ground_truth_mm_per_pixel": ground_truth_scale,
        "prediction_mm_per_pixel": prediction_scale,
        "absolute_error": absolute_error,
        "percentage_error": percentage_error
    }
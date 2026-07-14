class VisualGradeEngine:
    @staticmethod
    def get_grade(corrected_width_mm: float) -> str:
        if corrected_width_mm >= 2.0:
            return "CRITICAL / POOR"
        elif corrected_width_mm >= 1.0:
            return "SEVERE / MEDIUM"
        elif corrected_width_mm >= 0.3:
            return "MODERATE / GOOD"
        else:
            return "EXCELLENT"

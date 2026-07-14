class VisualReportFormatter:
    @staticmethod
    def generate_executive_summary(consensus: dict, context: dict) -> str:
        return (
            f"A visual inspection was conducted on the concrete element. "
            f"The assessment confirmed a primary anomaly classification of {consensus['primary_defect'].upper()} "
            f"with an integrated priority score of {consensus['flag_score']}/100. "
            f"Corrected measurements showed maximum surface cracks at {context['corrected_crack_width_mm']} mm. "
            f"The recommended action directive is set to {consensus['recommended_action'].upper()}."
        )

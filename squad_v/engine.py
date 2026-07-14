from .vi_v1 import VisualContextEngine
from .vi_v2 import VisualDefectEngine
from .vi_v3 import VisualConsensusEngine
from .utils import VisualReportFormatter
from .grade_engine import VisualGradeEngine

class VisualInspectionEngine:
    def __init__(self):
        self.context_eng = VisualContextEngine()
        self.defect_eng = VisualDefectEngine()
        self.consensus_eng = VisualConsensusEngine()

    def execute_pipeline(self, raw_width: float, element_type: str, lighting: str, access: str, grid_points: list) -> dict:
        # Step 1: Context processing (vi_v1)
        context = self.context_eng.process_context(element_type, raw_width, lighting, access)

        # Step 2: Extract local rule-based defects (vi_v2)
        local_defect = self.defect_eng.analyze_grid(grid_points, context)

        # Step 3: Core role-based prompting & evaluations (vi_v3)
        r1 = self.consensus_eng.call_claude_role(1, context, grid_points)
        r2 = self.consensus_eng.call_claude_role(2, context, grid_points)
        r3 = {
            "primary_defect": local_defect["primary_defect"],
            "flag_score": local_defect["flag_score"],
            "recommended_action": "escalate" if local_defect["flag_score"] > 80 else "monitor",
            "reasoning": "Determined strictly by localized physical rules engine algorithms."
        }

        # Step 4: Resolve consensus metrics (vi_v3)
        consensus = self.consensus_eng.resolve(r1, r2, r3)

        # Step 5: Gather final outputs
        grade = VisualGradeEngine.get_grade(context["corrected_crack_width_mm"])
        narrative = VisualReportFormatter.generate_executive_summary(consensus, context)

        return {
            "context": context,
            "consensus": consensus,
            "grade": grade,
            "narrative": narrative
        }

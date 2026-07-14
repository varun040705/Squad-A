import os
import sys
import traceback
from typing import List, Dict, Any

from dotenv import load_dotenv
load_dotenv()

# Import local pipeline engines
from squad_v.grade_engine import VisualGradeEngine
from squad_v.vi_v1 import VisualContextEngine
from squad_v.vi_v2 import VisualDefectEngine
from squad_v.vi_v3 import VisualConsensusEngine
from squad_v.report_generator import ReportGenerator


def run_structural_pipeline(
    element_type: str,
    raw_points: List[Dict[str, Any]],
    lighting: str,
    accessibility: str,
    critical_threshold: float = 1.5
) -> Dict[str, Any]:
    """
    Orchestrates the full visual inspection pipeline from raw sensor data
    to calibrated defects, grading tiers, and consensus-driven actions.
    """
    print(f"\n=== Running Pipeline for {element_type.upper()} ===")
    print(f"Parameters: Lighting={lighting} | Access={accessibility} | Critical Limit={critical_threshold}mm\n")

    # 1. Initialize Engines
    context_engine = VisualContextEngine()
    defect_engine = VisualDefectEngine()
    grade_engine = VisualGradeEngine()
    consensus_engine = VisualConsensusEngine()

    # 2. Calibration Stage
    calibrated_points = []
    for pt in raw_points:
        calibration_result = context_engine.process_context(
            element_type=element_type,
            raw_width_mm=pt["width_mm"],
            lighting_condition=lighting,
            accessibility_mode=accessibility
        )

        calibrated_points.append({
            "id": pt["id"],
            "width_mm": calibration_result["corrected_crack_width_mm"],
            "surface_roughness_index": pt.get("surface_roughness_index", 0.3)
        })

    print(f"[STAGE 1] Calibrated {len(raw_points)} points.")

    # 3. Defect Analysis Stage
    analysis_context = {
        "element_type": element_type,
        "effective_bands": {
            "critical": critical_threshold
        }
    }

    defect_result = defect_engine.analyze_grid(calibrated_points, analysis_context)
    detected_defect = defect_result["primary_defect"]
    max_calibrated_width = max(pt["width_mm"] for pt in calibrated_points)

    print(f"[STAGE 2] Defect Analysis Completed:")
    print(f"          - Primary Defect: {detected_defect.upper()}")
    print(f"          - Max Calibrated Width: {max_calibrated_width:.2f} mm")
    print(f"          - Initial Flag Score: {defect_result['flag_score']}")

    # 4. Severity Grading Stage
    severity_grade = grade_engine.get_grade(max_calibrated_width)
    print(f"[STAGE 3] Severity Grade: {severity_grade}")

    # 5. Consensus Stage
    role_drone_opinion = {
        "primary_defect": detected_defect,
        "confidence": "high" if accessibility == "DIRECT" else "medium",
        "recommended_action": "monitor" if severity_grade in ["EXCELLENT", "GOOD / SATISFACTORY"] else "retest",
        "flag_score": defect_result["flag_score"]
    }

    role_structural_lead_opinion = {
        "primary_defect": detected_defect if max_calibrated_width < critical_threshold else "crack",
        "confidence": "high",
        "recommended_action": "escalate" if max_calibrated_width >= critical_threshold else "flag_for_review",
        "flag_score": defect_result["flag_score"] + 15
    }

    role_materials_opinion = {
        "primary_defect": detected_defect,
        "confidence": "medium",
        "recommended_action": "monitor" if max_calibrated_width < 1.0 else "retest",
        "flag_score": defect_result["flag_score"] - 5
    }

    consensus_result = consensus_engine.resolve(
        role_drone_opinion,
        role_structural_lead_opinion,
        role_materials_opinion
    )

    print(f"[STAGE 4] Consensus Resolution:")
    print(f"          - Resolved Defect: {consensus_result['primary_defect'].upper()}")
    print(f"          - Final Action Item: {consensus_result['recommended_action'].upper()}")
    print(f"          - Aggregated Flag Score: {consensus_result['flag_score']}")
    print(f"          - Agreement Strength: {consensus_result['roles_agreed']}/3 roles\n")

    return {
        "element_type": element_type,
        "max_calibrated_width": max_calibrated_width,
        "severity_grade": severity_grade,
        "consensus": consensus_result
    }


if __name__ == "__main__":
    sample_technician_log = (
        "We are looking at Column B-12 on the main structural bay. "
        "The lighting here is a bit tricky, quite dusty on the surface which is messing with our camera glare slightly. "
        "We flew the remote UAV drone to capture this high up. "
        "We registered three physical cracks: the first point marked P01 has a width of 1.1mm. "
        "Point P02 is highly degraded, looking to be about 1.45mm. "
        "Point P03 seems stable at around 0.65mm."
    )

    # Static fallback measurements simulating what Claude extracts
    simulated_parsed_inputs = {
        "element_type": "COLUMN",
        "lighting": "DUSTY_SURFACE",
        "accessibility": "REMOTE_DRONE",
        "raw_points": [
            {"id": "P01", "width_mm": 1.1, "surface_roughness_index": 0.3},
            {"id": "P02", "width_mm": 1.45, "surface_roughness_index": 0.4},
            {"id": "P03", "width_mm": 0.65, "surface_roughness_index": 0.2}
        ]
    }

    pipeline_result = None

    # Decide whether to run the live Claude call or use fallback data
    if os.environ.get("ANTHROPIC_API_KEY"):
        from squad_v.llm_parser import LLMReasoningHook
        import anthropic

        print("=== Attempting Live LLM Parsing Layer with Claude ===")
        try:
            hook = LLMReasoningHook()
            parsed_inputs = hook.parse_field_report(sample_technician_log)
            print("[LLM SUCCESS] Raw field report successfully parsed by Claude.")

            pipeline_result = run_structural_pipeline(
                element_type=parsed_inputs["element_type"],
                raw_points=parsed_inputs["raw_points"],
                lighting=parsed_inputs["lighting"],
                accessibility=parsed_inputs["accessibility"]
            )
        except anthropic.BadRequestError as e:
            # Catch credit exhaustion or billing limits gracefully
            if "credit balance is too low" in str(e):
                print("\n[NOTE] Anthropic API key detected but developer account has low credits.")
                print(f"       Raw Exception: {e}")
                print("[FALLBACK] Executing local pipeline simulation with structured data mock...\n")
            else:
                print(f"\n[API ERROR] An API error occurred during processing:")
                print(f"Details: {e}")
                print("[FALLBACK] Proceeding with simulation fallback data...\n")

            pipeline_result = run_structural_pipeline(
                element_type=simulated_parsed_inputs["element_type"],
                raw_points=simulated_parsed_inputs["raw_points"],
                lighting=simulated_parsed_inputs["lighting"],
                accessibility=simulated_parsed_inputs["accessibility"]
            )
        except Exception as e:
            print("\n[UNEXPECTED ERROR] A system exception occurred in the processing wrapper:")
            traceback.print_exc()
            print("[FALLBACK] Executing pipeline with simulation fallback data...\n")
            pipeline_result = run_structural_pipeline(
                element_type=simulated_parsed_inputs["element_type"],
                raw_points=simulated_parsed_inputs["raw_points"],
                lighting=simulated_parsed_inputs["lighting"],
                accessibility=simulated_parsed_inputs["accessibility"]
            )
    else:
        print("=== Running with Simulated Fallback Data (No ANTHROPIC_API_KEY Found) ===")
        pipeline_result = run_structural_pipeline(
            element_type=simulated_parsed_inputs["element_type"],
            raw_points=simulated_parsed_inputs["raw_points"],
            lighting=simulated_parsed_inputs["lighting"],
            accessibility=simulated_parsed_inputs["accessibility"]
        )

    # ==========================================
    # DAY 3 TARGET: REPORT GENERATION DISPATCH
    # ==========================================
    if pipeline_result:
        print("\n=== [DAY 3] Commencing Report Generation ===")
        json_path = os.path.join("outputs", "inspection_report.json")
        md_path = os.path.join("outputs", "inspection_report.md")

        ReportGenerator.generate_json_report(pipeline_result, json_path)
        ReportGenerator.generate_markdown_report(pipeline_result, md_path)
        print("=== [DAY 3] Handoff Deliverables Generated Successfully! ===\n")

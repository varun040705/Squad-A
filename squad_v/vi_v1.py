import uuid
from typing import Dict, Any
from .config import ELEMENT_CEILINGS
from .models import VisualContextOutput

class VisualContextEngine:
    def process_context(
        self,
        element_type: str,
        raw_width_mm: float,
        lighting_condition: str,  # OPTIMAL, DAMP_LIGHT, DUSTY_SURFACE
        accessibility_mode: str   # DIRECT, REMOTE_DRONE
    ) -> Dict[str, Any]:

        element_key = element_type.upper()
        if element_key not in ELEMENT_CEILINGS:
            raise ValueError(f"Unsupported element type: {element_type}")

        corrected_width = raw_width_mm
        corrections_applied = []
        flags = []

        # 1. Environmental correction adjustments
        if lighting_condition.upper() == "DAMP_LIGHT":
            penalty = raw_width_mm * 0.08
            corrected_width += penalty
            corrections_applied.append({
                "type": "lighting",
                "factor": 0.08,
                "reason": "Low-contrast lighting compensation applied (+8% width scaling adjustment)"
            })
        elif lighting_condition.upper() == "DUSTY_SURFACE":
            penalty = raw_width_mm * 0.15
            corrected_width += penalty
            corrections_applied.append({
                "type": "surface_condition",
                "factor": 0.15,
                "reason": "Concrete dust surface masking penalty applied (+15% width scaling adjustment)"
            })

        # 2. Capture methodology limits[cite: 3]
        confidence_ceiling = ELEMENT_CEILINGS[element_key]
        if accessibility_mode.upper() == "REMOTE_DRONE":
            corrected_width += (raw_width_mm * 0.05)
            corrections_applied.append({
                "type": "accessibility",
                "factor": 0.05,
                "reason": "Drone camera angle correction applied (+5% width scaling adjustment)"
            })
            confidence_ceiling = min(confidence_ceiling, 65)
            flags.append("remote_drone_capture_active")

        # 3. Dynamic severity threshold bands[cite: 3]
        if element_key in ["COLUMN", "BEAM"]:
            effective_bands = {"critical": 2.0, "severe": 1.0, "moderate": 0.3}
        else:
            effective_bands = {"critical": 3.5, "severe": 2.0, "moderate": 1.0}

        if corrected_width > effective_bands["severe"]:
            flags.append("immediate_defect_risk_indicated")

        output_payload = {
            "success": True,
            "input_id": str(uuid.uuid4()),
            "raw_crack_width_mm": round(raw_width_mm, 3),
            "corrected_crack_width_mm": round(corrected_width, 3),
            "corrections_applied": corrections_applied,
            "effective_bands": effective_bands,
            "confidence_ceiling": confidence_ceiling,
            "flags": flags
        }

        return VisualContextOutput(**output_payload).model_dump()

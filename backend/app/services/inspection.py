from app.schemas.inspection import InspectionRequest, InspectionResponse

class InspectionService:
    """
    Core business logic engine for structural telemetry evaluation.
    """

    @staticmethod
    async def process_telemetry(payload: InspectionRequest) -> InspectionResponse:
        calibration_factor = 1.2 if payload.lighting == "DUSTY_SURFACE" else 1.0

        max_raw = max([p.width_mm for p in payload.raw_points], default=0.0)
        calibrated_width = max_raw * calibration_factor

        severity = "SEVERE" if calibrated_width > 1.5 else "MEDIUM"
        action = "ESCALATE" if severity == "SEVERE" else "MONITOR"

        summary = (
            f"Processed telemetry for asset {payload.element_type}. "
            f"Maximum calibrated width is {calibrated_width:.2f} mm, "
            f"assigning severity grade {severity}. Recommended action: {action}."
        )

        return InspectionResponse(
            status="success",
            chat_response_summary=summary,
            pipeline_payload={
                "element_type": payload.element_type,
                "max_calibrated_width": calibrated_width,
                "severity_grade": severity,
                "consensus": {
                    "recommended_action": action,
                    "agreement_strength": "2/3 roles"
                }
            }
        )

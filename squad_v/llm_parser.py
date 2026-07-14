import os
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from anthropic import Anthropic


# 1. Define the schema we expect back from the LLM
class SensorPoint(BaseModel):
    id: str = Field(description="Unique identifier for the measurement point, e.g., P01, P02")
    width_mm: float = Field(description="Raw measured crack width in millimeters")
    surface_roughness_index: float = Field(
        default=0.3,
        description="Estimated surface roughness index between 0.0 and 1.0. Default to 0.3 if not mentioned."
    )

class InspectionDataSchema(BaseModel):
    element_type: str = Field(
        description="The structural element being inspected. Must be COLUMN, BEAM, SLAB, or WALL."
    )
    lighting: str = Field(
        description="Lighting quality. Choose from: STANDARD, DUSTY_SURFACE, LOW_LIGHT, GLARE."
    )
    accessibility: str = Field(
        description="Access type. Choose from: DIRECT, REMOTE_DRONE, DIFFICULT_ANGLE."
    )
    raw_points: List[SensorPoint] = Field(
        description="List of raw physical points extracted from the text."
    )


# 2. Build the parser client
class LLMReasoningHook:
    def __init__(self):
        # Initializes the client using the ANTHROPIC_API_KEY environment variable
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def parse_field_report(self, raw_report: str) -> Dict[str, Any]:
        """
        Parses raw text observations into structured schema inputs for the visual pipeline.
        """
        print("[LLM] Processing unstructured field report with Claude...")

        # We instruct Claude using a tool schema constraint to ensure structural alignment
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0.0,  # Highly deterministic parsing
            system="You are an expert structural forensic AI. Your job is to extract exact measurements, conditions, and element types from messy technician field logs.",
            messages=[
                {"role": "user", "content": f"Please extract the structured data from this report:\n\n{raw_report}"}
            ],
            tools=[
                {
                    "name": "format_inspection_data",
                    "description": "Format extracted structural inspection measurements into a clean schema.",
                    "input_schema": InspectionDataSchema.model_json_schema()
                }
            ],
            tool_choice={"type": "tool", "name": "format_inspection_data"}
        )

        # Extract the structured tool inputs directly from the message block
        for content_block in response.content:
            if content_block.type == "tool_use" and content_block.name == "format_inspection_data":
                return content_block.input

        raise ValueError("Failed to obtain structured tool output from the model.")

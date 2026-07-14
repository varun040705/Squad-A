import json
from collections import Counter
from anthropic import Anthropic
from .config import ANTHROPIC_API_KEY
from .models import ClaudeResponseSchema

class VisualConsensusEngine:
    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.tool_schema = {
            "name": "respond_with_defect_analysis",
            "description": "Outputs a deterministic visual defect evaluation based on structural rules.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "primary_defect": {"type": "string", "description": "Name of the defect identified."},
                    "flag_score": {"type": "integer", "description": "Priority score from 0 to 100."},
                    "recommended_action": {"type": "string", "description": "Recommended engineering action category."},
                    "reasoning": {"type": "string", "description": "Detailed engineering evaluation without hedging words."}
                },
                "required": ["primary_defect", "flag_score", "recommended_action", "reasoning"]
            }
        }

    def get_role_prompt(self, role_id: int, context_json: str, grid_json: str) -> str:
        roles = {
            1: "You are an IS Code Compliance Assessor. Evaluate visual anomalies strictly against safety rules.",
            2: "You are a Spatial Structural Analyst. Focus on geometric patterns and coordinate paths of defects.",
            3: "You are a Historical Material Comparator. Compare visual changes against tracking metrics."
        }
        return f"""
        {roles.get(role_id, "You are an expert structural engineer.")}

        CRITICAL RULES:
        - Never estimate compressive strength or output values in MPa[cite: 3].
        - Never declare an element 'safe' or 'unsafe'. That is a licensed engineer's call[cite: 3].
        - Speak with absolute certainty. Never use hedging words like: 'possibly', 'might', 'could be'[cite: 3].

        CONTEXT AND THRESHOLDS:
        {context_json}

        MEASUREMENT GRID POINT DATA:
        {grid_json}
        """

    def call_claude_role(self, role_id: int, context_data: dict, grid_data: list) -> dict:
        prompt = self.get_role_prompt(role_id, json.dumps(context_data), json.dumps(grid_data))
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                temperature=0.0,  # Zero variance temperature
                system="You are a data parsing engine that outputs exclusively via structured tool selection.",
                messages=[{"role": "user", "content": prompt}],
                tools=[self.tool_schema],
                tool_choice={"type": "tool", "name": "respond_with_defect_analysis"}
            )
            raw_input = response.content[0].input
            return ClaudeResponseSchema(**raw_input).model_dump()
        except Exception as e:
            return {
                "primary_defect": "uncertain",
                "flag_score": 50,
                "recommended_action": "flag_for_review",
                "reasoning": f"Fallback executed. Claude API processing bypassed: {str(e)}"
            }

    def resolve(self, r1: dict, r2: dict, r3: dict) -> dict:
        defects = [r1["primary_defect"], r2["primary_defect"], r3["primary_defect"]]
        actions = [r["recommended_action"] for r in [r1, r2, r3]]

        top_defect, top_count = Counter(defects).most_common(1)[0]
        severity_hierarchy = ["pass", "monitor", "retest", "flag_for_review", "escalate"]
        final_action = max(actions, key=lambda a: severity_hierarchy.index(a) if a in severity_hierarchy else 0)

        if top_count == 3:
            confidence = "high"
        elif top_count == 2:
            confidence = "medium"
        else:
            top_defect = "uncertain"
            final_action = "flag_for_review"
            confidence = "low"

        mean_flag_score = round((r1["flag_score"] + r2["flag_score"] + r3["flag_score"]) / 3)

        return {
            "primary_defect": top_defect,
            "flag_score": mean_flag_score,
            "confidence": confidence,
            "recommended_action": final_action,
            "roles_agreed": top_count
        }

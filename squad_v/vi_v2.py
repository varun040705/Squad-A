from typing import List, Dict, Any, Optional

class VisualDefectEngine:
    @staticmethod
    def detect_honeycombing(grid_points: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Rule: 3+ adjacent points with severe surface voids and high surface roughness[cite: 3]
        """
        affected_points = []
        for pt in grid_points:
            if pt.get("surface_roughness_index", 0.0) > 0.7 and pt.get("width_mm", 0.0) >= 1.5:
                affected_points.append(pt["id"])

        if len(affected_points) >= 3:
            return {
                "primary_defect": "honeycombing",
                "defect_location": affected_points,
                "flag_score": 85
            }
        return None

    @staticmethod
    def detect_structural_crack(grid_points: List[Dict[str, Any]], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Rule: Points forming a continuous trajectory that exceed the critical width threshold[cite: 3]
        """
        critical_threshold = context["effective_bands"]["critical"]
        severe_points = [pt["id"] for pt in grid_points if pt.get("width_mm", 0.0) >= critical_threshold]

        if len(severe_points) >= 2:
            return {
                "primary_defect": "structural_crack",
                "defect_location": severe_points,
                "flag_score": 95
            }
        return None

    def analyze_grid(self, grid_points: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        crack_diagnosis = self.detect_structural_crack(grid_points, context)
        if crack_diagnosis:
            return crack_diagnosis

        honeycomb_diagnosis = self.detect_honeycombing(grid_points)
        if honeycomb_diagnosis:
            return honeycomb_diagnosis

        return {
            "primary_defect": "none",
            "defect_location": [],
            "flag_score": 10
        }

import pytest
from squad_v.grade_engine import VisualGradeEngine

def test_grading_thresholds():
    grader = VisualGradeEngine()

    # 0.2 mm is graded as EXCELLENT by your engine
    assert grader.get_grade(0.2) == "EXCELLENT"

    # 1.2 mm
    assert grader.get_grade(1.2) == "SEVERE / MEDIUM"

    # 2.5 mm
    assert grader.get_grade(2.5) == "CRITICAL / POOR"

"""
grade_engine.py

Determines the Acoustic Emission grade.

Author: Sai Varun
Project: OX1 - Squad H
"""

from squad_h.models import H2Result, AEGrade, TrendType


def determine_grade(h2_result: H2Result) -> AEGrade:

    if not h2_result.localization.success:
        return AEGrade.IV

    if h2_result.trend.trend == TrendType.INSUFFICIENT_DATA:
        return AEGrade.III

    if h2_result.trend.trend == TrendType.STABLE:
        return AEGrade.II

    return AEGrade.I
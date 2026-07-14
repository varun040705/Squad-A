"""
test_h3.py
"""
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from squad_h.models import (
    LocalizationResult,
    TrendResult,
    LoadHistoryResult,
    H2Result,
    TrendType,
)

from squad_h.ae_h3 import build_context


def test_context_builder():

    h2 = H2Result(

        localization=LocalizationResult(
            success=False,
            x=None,
            y=None,
            z=None,
            sensors_used=1,
            message="Failed",
        ),

        trend=TrendResult(
            b_value=None,
            trend=TrendType.INSUFFICIENT_DATA,
            confidence=0,
        ),

        load_history=LoadHistoryResult(),

        total_hits=2,
        eligible_hits=1,
    )

    context = build_context(
        "AE-001",
        h2,
    )

    assert context.inspection_id == "AE-001"
    assert context.total_hits == 2
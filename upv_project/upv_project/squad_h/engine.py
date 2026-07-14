"""
engine.py

Main AE Engine

Author: Sai Varun
Project: OX1 - Squad H
"""

from squad_h.ae_h1 import preprocess_and_detect_hits
from squad_h.ae_h2 import analyze_ae
from squad_h.ae_h3 import build_context


def run_ae_engine(
    inspection_id: str,
    hits,
):
    """
    Complete AE processing pipeline.
    """

    h1_result = preprocess_and_detect_hits(hits)

    h2_result = analyze_ae(h1_result)

    context = build_context(
        inspection_id,
        h2_result,
    )

    return context
import pytest
from squad_v.vi_v3 import VisualConsensusEngine

def test_consensus_local_rule_fallback():
    engine = VisualConsensusEngine()
    r1 = {
        "primary_defect": "crack",
        "confidence": "high",
        "recommended_action": "monitor",
        "flag_score": 10
    }
    r2 = {
        "primary_defect": "crack",
        "confidence": "medium",
        "recommended_action": "monitor",
        "flag_score": 20
    }
    r3 = {
        "primary_defect": "spalling",
        "confidence": "low",
        "recommended_action": "epoxy_inject",
        "flag_score": 30
    }

    resolution = engine.resolve(r1, r2, r3)
    assert resolution["primary_defect"] == "crack"
    assert resolution["roles_agreed"] == 2

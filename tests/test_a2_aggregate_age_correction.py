import pytest
from uuid import uuid4

from modules.upv.a2_aggregate_age_correction import (
    get_effective_bands,
    compute_ami,
    assemble_context,
    AggregateType
)


def test_lightweight_bands():

    bands = get_effective_bands(
        AggregateType.lightweight
    )

    assert bands["excellent"] == 3.2
    assert bands["good"] == 2.5
    assert bands["medium"] == 2.0
    assert bands["poor"] == 1.8


def test_ami_no_flag():

    ami, flag = compute_ami(
        v_actual=3.2,
        age_days=7,
        v_28day_reference=4.3
    )

    assert round(ami, 3) == 1.006
    assert flag is False


def test_ami_flag():

    ami, flag = compute_ami(
        v_actual=2.5,
        age_days=7,
        v_28day_reference=4.3
    )

    assert round(ami, 3) == 0.786
    assert flag is True


def test_unknown_age():

    ami, flag = compute_ami(
        v_actual=3.0,
        age_days=21,
        v_28day_reference=4.3
    )

    assert ami is None
    assert flag is True


def test_assemble_context():

    result = assemble_context(
        {
            "element_id": uuid4(),
            "aggregate_type": "lightweight",
            "concrete_age_days": 7,
            "raw_velocity_kmps": 3.2,
            "v_28day_reference": 4.3
        }
    )

    assert result.effective_bands["good"] == 2.5
    assert result.age_underperformance is False
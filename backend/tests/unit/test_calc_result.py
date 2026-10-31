import pytest
from pydantic import ValidationError

from app.domain.calc_result import CalcResult, Confidence, ResultStatus


def _ok(**kw):
    base = {
        "name": "electrical.power",
        "value": 12.0,
        "unit": "W",
        "formula": "P = U × I",
        "inputs": {"U_v": 12.0, "I_a": 1.0},
        "status": ResultStatus.THEORETICAL,
        "confidence": Confidence.HIGH,
    }
    return CalcResult(**{**base, **kw})


def test_valid_result():
    r = _ok()
    assert r.value == 12.0 and r.unit == "W"


def test_value_none_requires_not_evaluable():
    with pytest.raises(ValidationError):
        _ok(value=None)


def test_not_evaluable_must_have_no_value():
    with pytest.raises(ValidationError):
        _ok(status=ResultStatus.NOT_EVALUABLE, missing_inputs=["I_a"])


def test_not_evaluable_requires_missing_or_limits():
    with pytest.raises(ValidationError):
        CalcResult(name="x", value=None, unit="W", formula="f", status=ResultStatus.NOT_EVALUABLE)


def test_not_evaluable_factory():
    r = CalcResult.not_evaluable(
        name="electrical.power", unit="W", formula="P = U × I", missing_inputs=["I_a"]
    )
    assert r.value is None
    assert r.status is ResultStatus.NOT_EVALUABLE
    assert r.missing_inputs == ["I_a"]


def test_result_is_immutable():
    r = _ok()
    with pytest.raises(ValidationError):
        r.value = 1.0

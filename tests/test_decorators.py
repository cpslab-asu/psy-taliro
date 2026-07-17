from __future__ import annotations

import pytest
import typing_extensions

from staliro import Result, Sample, Trace, decorators
from staliro.cost_func import CostFunc, Inputs, Signals
from staliro.models import Blackbox, BlackboxInputs, Model
from staliro.signals import UnboundInterval
from staliro.specifications import Specification


@pytest.fixture
def i() -> Inputs:
    return Inputs(Sample([]), {}, Signals({}, UnboundInterval()))


@pytest.fixture
def t() -> Trace[int]:
    return Trace(times=[], states=[])


def test_ensure_result() -> None:
    r1 = typing_extensions.assert_type(decorators.ensure_result(1.0), Result[float, None])

    assert isinstance(r1, Result)
    assert r1.value == 1.0
    assert r1.extra is None

    r2: Result[float, str | None] = typing_extensions.assert_type(
        decorators.ensure_result(Result(1.0, "foo")), Result[float, str | None]
    )

    assert isinstance(r2, Result)
    assert r2.value == 1.0
    assert r2.extra == "foo"


def test_costfunc(i: Inputs) -> None:
    @decorators.costfunc
    def cf1(s: Inputs) -> int:
        return 0

    assert isinstance(cf1, CostFunc)

    @decorators.costfunc
    def cf2(s: Inputs) -> Result[int, str]:
        return Result(0, "foo")

    assert isinstance(cf2, CostFunc)

    r1 = typing_extensions.assert_type(cf1.evaluate(i), Result[int, None])

    assert isinstance(r1, Result)
    assert isinstance(r1.value, int)
    assert r1.extra is None

    r2 = typing_extensions.assert_type(cf2.evaluate(i), Result[int, str])

    assert isinstance(r2, Result)
    assert isinstance(r2.value, int)
    assert r2.extra == "foo"


def test_model(i: Inputs) -> None:
    @decorators.model
    def m1(s: Inputs) -> Trace[int]:
        return Trace(times=[], states=[])

    assert isinstance(m1, Model)

    @decorators.model
    def m2(s: Inputs) -> Result[Trace[int], str]:
        return Result(Trace[int](times=[], states=[]), "foo")

    assert isinstance(m2, Model)

    t1 = typing_extensions.assert_type(m1.simulate(i), Result[Trace[int], None])

    assert isinstance(t1, Result)
    assert isinstance(t1.value, Trace)
    assert t1.extra is None

    t2 = typing_extensions.assert_type(m2.simulate(i), Result[Trace[int], str])

    assert isinstance(t2, Result)
    assert isinstance(t2.value, Trace)
    assert t2.extra == "foo"


def test_blackbox(i: Inputs) -> None:
    @decorators.blackbox(step_size=0.1)
    def bb1(s: BlackboxInputs) -> Trace[int]:
        return Trace(times=[], states=[])

    assert isinstance(bb1, Blackbox)
    assert bb1.step_size == 0.1

    @decorators.blackbox(step_size=0.01)
    def bb2(s: BlackboxInputs) -> Result[Trace[int], str]:
        return Result(Trace[int](times=[], states=[]), "foo")

    assert isinstance(bb2, Blackbox)
    assert bb2.step_size == 0.01

    t1 = typing_extensions.assert_type(bb1.simulate(i), Result[Trace[int], None])

    assert isinstance(t1, Result)
    assert isinstance(t1.value, Trace)
    assert t1.extra is None

    t2 = typing_extensions.assert_type(bb2.simulate(i), Result[Trace[int], str])

    assert isinstance(t2, Result)
    assert isinstance(t2.value, Trace)
    assert t2.extra == "foo"


def test_specification(t: Trace[int]) -> None:
    @decorators.specification
    def s1(t: Trace[int]) -> float:
        return 0.0

    assert isinstance(s1, Specification)

    @decorators.specification
    def s2(t: Trace[int]) -> Result[float, str]:
        return Result(0.0, "foo")

    assert isinstance(s2, Specification)

    c1 = typing_extensions.assert_type(s1.evaluate(t), Result[float, None])

    assert isinstance(c1, Result)
    assert isinstance(c1.value, float)
    assert c1.extra is None

    c2 = typing_extensions.assert_type(s2.evaluate(t), Result[float, str])

    assert isinstance(c2, Result)
    assert isinstance(c2.value, float)
    assert c2.extra == "foo"

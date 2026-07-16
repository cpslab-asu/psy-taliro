from collections.abc import Iterable

import attrs
import numpy as np
import pytest
import typing_extensions as te

from staliro.optimizers import Sample
from staliro.options import SignalInput, TestOptions, _to_interval
from staliro.signals import Interval, Signal


def test_interval_conversion() -> None:
    assert _to_interval([1, 2]) == Interval(1, 2)
    assert _to_interval((1, 2)) == Interval(1, 2)
    assert _to_interval(np.array([1, 2])) == Interval(1, 2)
    assert _to_interval(Interval(1, 2)) == Interval(1, 2)


def test_static_inputs() -> None:
    options = TestOptions(static_inputs={"x": [0, 1], "y": (2, 4), "z": np.array([3, 7])})

    assert options.static_inputs["x"] == Interval(0, 1)
    assert options.static_inputs["y"] == Interval(2, 4)
    assert options.static_inputs["z"] == Interval(3, 7)


def test_seed() -> None:
    options = TestOptions()
    assert options.seed >= 0 and options.seed <= (2**32 - 1)


def test_processes() -> None:
    none = TestOptions()
    assert none.processes is None

    num = TestOptions(processes=4)
    assert num.processes == 4

    with pytest.raises(ValueError):
        TestOptions(processes=-1)

    _ = TestOptions(processes="cores")

    with pytest.raises(ValueError):
        TestOptions(processes="foo")  # type: ignore


def test_threads() -> None:
    none = TestOptions()
    assert none.threads is None

    num = TestOptions(threads=4)
    assert num.threads == 4

    with pytest.raises(ValueError):
        TestOptions(threads=-1)

    _ = TestOptions(threads="cores")

    with pytest.raises(ValueError):
        TestOptions(threads="foo")  # type: ignore


def test_control_points() -> None:
    with_times = SignalInput(control_points={0.1: [8, 12.5], 3.2: (0, 2.1)})
    assert with_times.control_points == {0.1: Interval(8, 12.5), 3.2: Interval(0, 2.1)}

    without_times = SignalInput(control_points=[[8, 12.5], (0, 2.1)])
    assert without_times.control_points == [Interval(8, 12.5), Interval(0, 2.1)]


@attrs.define()
class DummySignal(Signal):
    times: list[float]
    values: list[float]

    @te.override
    def at_time(self, time: float) -> float:
        raise NotImplementedError()


def dummy(times: Iterable[float], values: Iterable[float]) -> DummySignal:
    return DummySignal(list(times), list(values))


def test_parse_sample() -> None:
    options = TestOptions(
        tspan=(0.0, 100.0),
        static_inputs={
            "foo": (0, 1),
            "bar": (3, 4),
        },
        signals={
            "spam": SignalInput(
                control_points=[(0.0, 1.0), (1.0, 2.0)],
                factory=dummy,
            ),
            "eggs": SignalInput(
                control_points={33.0: (0.0, 1.0), 66.0: (1.0, 2.0)},
                factory=dummy,
            ),
        }
    )

    sample = Sample([0.0, 3.8, 0.5, 1.2, 0.2, 1.8])
    inputs = options.parse_sample(sample)

    assert inputs.static["foo"] == 0.0
    assert inputs.static["bar"] == 3.8

    spam = inputs.signals["spam"]
    assert isinstance(spam, DummySignal)
    assert spam.times == [0.0, 50.0]
    assert spam.values == [0.5, 1.2]

    eggs = inputs.signals["eggs"]
    assert isinstance(eggs, DummySignal)
    assert eggs.times == [33.0, 66.0]
    assert eggs.values == [0.2, 1.8]

from collections.abc import Iterable

from numpy import array

from staliro import Sample, Signal, SignalInput, TestOptions


def test_static() -> None:
    options = TestOptions(
        static_inputs={
            "a": (0.5, 1.5),
            "b": (2.8, 4.0),
            "c": (1.6, 8.4),
            "d": (3.0, 5.0),
        }
    )
    sample = Sample([1.0, 3.0, 2.0, 4.0], options)

    assert len(sample.signals) == 0
    assert len(sample.static) == 4

    assert sample.static["a"] == 1.0
    assert sample.static["b"] == 3.0
    assert sample.static["c"] == 2.0
    assert sample.static["d"] == 4.0


class TestSignal(Signal):
    def __init__(self, times: list[float], values: list[float]):
        self.times = times
        self.values = values

    def __repr__(self) -> str:
        return f"TestSignal(times={self.times}, values={self.values})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TestSignal):
            return NotImplemented

        return self.times == other.times and self.values == other.values

    def at_time(self, time: float) -> float:
        raise NotImplementedError()


def test_signals() -> None:
    def factory(times: Iterable[float], values: Iterable[float]) -> TestSignal:
        return TestSignal(list(times), list(values))

    options = TestOptions(
        tspan=(0, 12),
        signals={
            "rho": SignalInput(control_points=[(0, 1)] * 3, factory=factory),
            "phi": SignalInput(control_points=[(0, 1)] * 4, factory=factory),
        },
    )

    sample = Sample(
        values=[1.0, 3.0, 2.0, 4.0, 3.1, 2.9, 4.1],
        opts=options
    )

    assert len(sample.static) == 0
    assert len(sample.signals) == 2

    assert sample.signals.tspan == (0, 12)
    assert list(sample.signals.names) == ["rho", "phi"]
    assert sample.signals["rho"] == TestSignal([0, 4, 8], [1.0, 3.0, 2.0])
    assert sample.signals["phi"] == TestSignal([0, 3, 6, 9], [4.0, 3.1, 2.9, 4.1])


def test_values() -> None:
    options = TestOptions()

    s1 = Sample([1, 2, 3, 4], options)
    s2 = Sample(array([4, 3, 2, 1]), options)

    assert s1.values == [1, 2, 3, 4]
    assert s2.values == [4, 3, 2, 1]

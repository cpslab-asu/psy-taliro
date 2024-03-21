from collections.abc import Iterable

from pytest import fixture

from staliro import Result, Sample, Signal, SignalInput, TestOptions, Trace
from staliro.models import Blackbox, Model, Ode, blackbox, model, ode


class TestSignal(Signal):
    def at_time(self, time: float) -> float:
        return -time


@fixture
def sample() -> Sample:
    def factory(times: Iterable[float], values: Iterable[float]) -> Signal:
        return TestSignal()

    options = TestOptions(
        static_inputs={"rho": (0, 5)},
        tspan=(0, 10),
        signals={
            "phi": SignalInput(control_points=[(0, 1), (1, 2)], factory=factory),
        },
    )

    return Sample([3.2, 0.8, 1.3], options)


def test_model(sample: Sample) -> None:
    @model()
    def f1(_: Sample) -> Result[Trace[float], str]:
        return Result(Trace(times=[4, 3, 2, 1], states=[1, 2, 3, 4]), "foo")

    @model()
    def f2(_: Sample) -> Trace[float]:
        return Trace(times=[1, 2, 3, 4], states=[4, 3, 2, 1])

    assert isinstance(f1, Model)
    assert isinstance(f2, Model)

    r1 = f1.simulate(sample)
    assert isinstance(r1, Result)
    assert r1.value == Trace(times=[4, 3, 2, 1], states=[1, 2, 3, 4])
    assert r1.extra == "foo"

    r2 = f2.simulate(sample)
    assert isinstance(r2, Result)
    assert r2.value == Trace(times=[1, 2, 3, 4], states=[4, 3, 2, 1])
    assert r2.extra is None


def test_blackbox(sample: Sample) -> None:
    @blackbox()
    def f1(_: Blackbox.Inputs) -> Trace[float]:
        return Trace(times=[1, 2, 3, 4], states=[4, 3, 2, 1])

    @blackbox(step_size=1.0)
    def f2(inputs: Blackbox.Inputs) -> Result[Trace[float], Blackbox.Inputs]:
        return Result(Trace(times=[4, 3, 2, 1], states=[1, 2, 3, 4]), inputs)

    assert isinstance(f1, Blackbox)
    assert isinstance(f2, Blackbox)

    r1 = f1.simulate(sample)
    assert isinstance(r1, Result)
    assert r1.value == Trace(times=[1, 2, 3, 4], states=[4, 3, 2, 1])
    assert r1.extra is None

    r2 = f2.simulate(sample)
    assert isinstance(r2, Result)
    assert f2.step_size == 1.0
    assert r2.value == Trace(times=[4, 3, 2, 1], states=[1, 2, 3, 4])
    assert r2.extra.static == {"rho": 3.2}
    assert r2.extra.static["rho"] == 3.2
    assert r2.extra.times == {
        0.0: {"phi": 0.0},
        1.0: {"phi": -1.0},
        2.0: {"phi": -2.0},
        3.0: {"phi": -3.0},
        4.0: {"phi": -4.0},
        5.0: {"phi": -5.0},
        6.0: {"phi": -6.0},
        7.0: {"phi": -7.0},
        8.0: {"phi": -8.0},
        9.0: {"phi": -9.0},
        10.0: {"phi": -10.0},
    }


def test_ode(sample: Sample) -> None:
    @ode(method="RK45")
    def f(_: Ode.Inputs) -> dict[str, float]:
        raise NotImplementedError()

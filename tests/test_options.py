import numpy as np
import pytest

from staliro.options import SignalInput, TestOptions, _to_interval


def test_interval_conversion() -> None:
    assert _to_interval([1, 2]) == (1, 2)
    assert _to_interval((1, 2)) == (1, 2)
    assert _to_interval(np.array([1, 2])) == (1, 2)


def test_static_inputs() -> None:
    options = TestOptions(static_inputs={"x": [0, 1], "y": (2, 4), "z": np.array([3, 7])})

    print(options)

    assert options.static_inputs["x"] == (0, 1)
    assert options.static_inputs["y"] == (2, 4)
    assert options.static_inputs["z"] == (3, 7)


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
    assert with_times.control_points == {0.1: (8, 12.5), 3.2: (0, 2.1)}

    without_times = SignalInput(control_points=[[8, 12.5], (0, 2.1)])
    assert without_times.control_points == [(8, 12.5), (0, 2.1)]

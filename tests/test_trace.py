import numpy as np
import pytest
from sortedcontainers import SortedDict

from staliro import Trace


def test_from_times_states() -> None:
    t1 = Trace(times=[1.0, 2.0, 3.0], states=("a", "b", "c"))
    assert t1.elements == SortedDict({1.0: "a", 2.0: "b", 3.0: "c"})

    t2 = Trace(times=np.array([1.0, 2.0, 3.0]), states=["foo", "bar", "baz"])
    assert t2.elements == SortedDict({1.0: "foo", 2.0: "bar", 3.0: "baz"})

    with pytest.raises(TypeError):
        Trace(times=[[1.0], [2.0], [3.0]], states=(1, 2, 3))  # type: ignore

    with pytest.raises(ValueError):
        Trace(times=[1.0, 2.0, 3.0], states=(1, 2))


def test_from_states() -> None:
    t = Trace({1.0: "a", 2.0: "b", 3.0: "c"})
    assert t.elements == SortedDict({1.0: "a", 2.0: "b", 3.0: "c"})

    with pytest.raises(ValueError):
        Trace([1.0, 2.0, 3.0])  # type: ignore


def test_states() -> None:
    t1 = Trace({1.0: "a", 2.0: "b", 3.0: "c"})
    assert list(t1.states) == ["a", "b", "c"]

    t2 = Trace({3.0: "c", 1.0: "a", 2.0: "b"})
    assert list(t2.states) == ["a", "b", "c"]


def test_times() -> None:
    t1 = Trace({1.0: "a", 2.0: "b", 3.0: "c"})
    assert list(t1.times) == [1.0, 2.0, 3.0]

    t2 = Trace({3.0: "c", 1.0: "a", 2.0: "b"})
    assert list(t2.times) == [1.0, 2.0, 3.0]


def test_length() -> None:
    t1 = Trace({1.0: "a", 2.0: "b", 3.0: "c", 4.0: "d"})
    assert len(t1) == 4

    t2 = Trace({3.0: "c", 1.0: "a", 2.0: "b"})
    assert len(t2) == 3


def test_eq() -> None:
    t1 = Trace({1.0: "a", 2.0: "b", 3.0: "c", 4.0: "d"})
    t2 = Trace({3.0: "c", 1.0: "a", 2.0: "b"})
    t3 = Trace({3.0: "c", 1.0: "a", 2.0: "b"})

    assert t2 == t3
    assert t1 != t2


def test_idx() -> None:
    t = Trace({1.0: "a", 2.0: "b", 3.0: "c", 4.0: "d"})

    assert t[1.0] == "a"
    assert t[4.0] == "d"

    with pytest.raises(KeyError):
        t[5.0]

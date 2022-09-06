from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Sequence, TypeVar

from attr import frozen

from .interval import Interval
from .signal import Signal

StateT = TypeVar("StateT")
ExtraT = TypeVar("ExtraT")


@frozen(eq=False)
class Trace(Generic[StateT]):
    _times: Sequence[float]
    _states: Sequence[StateT]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Trace):
            return NotImplemented

        return self.times == other.times and self.states == other.states

    def __len__(self) -> int:
        return len(self._times)

    @property
    def times(self) -> list[float]:
        return list(self._times)

    @property
    def states(self) -> list[StateT]:
        return list(self._states)


class ModelResult(Generic[StateT, ExtraT], ABC):
    @property
    @abstractmethod
    def trace(self) -> Trace[StateT]:
        ...

    @property
    @abstractmethod
    def extra(self) -> ExtraT:
        ...


class BasicResult(ModelResult[StateT, None]):
    def __init__(self, trace: Trace[StateT]):
        self._trace = trace

    @property
    def trace(self) -> Trace[StateT]:
        return self._trace

    @property
    def extra(self) -> None:
        return None


class ExtraResult(ModelResult[StateT, ExtraT]):
    def __init__(self, trace: Trace[StateT], extra: ExtraT):
        self._trace = trace
        self._extra = extra

    @property
    def trace(self) -> Trace[StateT]:
        return self._trace

    @property
    def extra(self) -> ExtraT:
        return self._extra


class FailureResult(ModelResult[StateT, ExtraT]):
    def __init__(self, extra: ExtraT):
        self._extra = extra

    @property
    def trace(self) -> Trace[StateT]:
        return Trace([], [])

    @property
    def extra(self) -> ExtraT:
        return self._extra


@frozen()
class ModelInputs:
    static: Sequence[float]
    signals: Sequence[Signal]


class Model(Generic[StateT, ExtraT], ABC):
    """A model is a representation of a system under test (SUT).

    The model defines a simulate method that contains the logic necessary to simulate the system
    given a set of inputs.
    """

    @abstractmethod
    def simulate(self, inputs: ModelInputs, interval: Interval) -> ModelResult[StateT, ExtraT]:
        """Simulate the model using the given inputs.

        This method contains the logic responsible for simulating the model with the given inputs.
        The result of this method should be a ModelResult instance containing a set of timestamps
        and state values representing the execution of the system over time, or a Failure instance
        that serves as an indicator of a system failure that should be interpreted as a
        falsification of the system requirement.

        Arguments:
            static: The static inputs to the system
            signals: time-varying inputs to the system represented as interpolated functions

        Returns:
            An instance of ModelData indicating a successful simulation, or a Failure if an error is
            encountered that should result in a falsification.
        """
        ...


class ModelError(Exception):
    pass

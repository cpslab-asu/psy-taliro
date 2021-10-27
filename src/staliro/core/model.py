from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, Sequence, TypeVar, Union, overload

import numpy as np
from attr import Attribute, field, frozen
from numpy.typing import NDArray

from .interval import Interval
from .signal import Signal


Times = NDArray[np.float_]


def _times_validator(obj: Any, attr: Attribute[Any], times: Times) -> None:
    if not isinstance(times, np.ndarray):
        raise TypeError("timestamps must be provided as a NDArray")

    if not np.issubdtype(times.dtype, np.floating):
        raise TypeError("timestamp values must be floating point values")

    if times.ndim != 1:
        raise ValueError("timestamps must be 1-dimensional")


StateT = TypeVar("StateT")
ExtraT = TypeVar("ExtraT")


@frozen(init=False)
class ModelData(Generic[StateT, ExtraT]):
    """Representation of the state of a system over time.

    Attributes:
        times: The timestamps corresponding to each state of the system
        extra: User-defined data related to the particular system execution
    """

    states: StateT
    times: Times = field(validator=_times_validator, converter=np.array)
    extra: ExtraT

    @overload
    def __init__(self: ModelData[StateT, None], states: StateT, timestamps: Any):
        ...

    @overload
    def __init__(self, states: StateT, timestamps: Any, extra: ExtraT):
        ...

    def __init__(self, states: StateT, timestamps: Any, extra: ExtraT = None):
        self.__attrs_init__(states, timestamps, extra)  # type: ignore


@frozen(init=False)
class Failure(Generic[ExtraT]):
    """Representation of a system failure that should be interpreted as a falsification.

    Attributes:
        extra: User-defined data related to the particular system execution
    """

    extra: ExtraT = field()

    @overload
    def __init__(self: Failure[None]):
        ...

    @overload
    def __init__(self, extra: ExtraT):
        ...

    def __init__(self, extra: ExtraT = None):
        self.__attrs_init__(extra)  # type: ignore


StaticInput = Sequence[float]
Signals = Sequence[Signal]
ModelResult = Union[ModelData[StateT, ExtraT], Failure[ExtraT]]


class Model(Generic[StateT, ExtraT], ABC):
    """A model is a representation of a system under test (SUT).

    The model defines a simulate method that contains the logic necessary to simulate the system
    given a set of inputs.
    """

    @abstractmethod
    def simulate(
        self, static: StaticInput, signals: Signals, interval: Interval
    ) -> ModelResult[StateT, ExtraT]:
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

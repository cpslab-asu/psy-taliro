from __future__ import annotations

import math
import sys
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, Union, Optional, Type, TYPE_CHECKING, Tuple

if sys.version_info >= (3, 9):
    from collections.abc import Sequence, Callable
else:
    from typing import Sequence, Callable

import numpy as np
from attr import Attribute, attrs, attrib
from numpy.typing import NDArray
from scipy import integrate
from typing_extensions import overload

from .options import Interval
from .signals import SignalInterpolator
from .specification import Specification

if TYPE_CHECKING:
    _Validator = Callable[[Any, Attribute[Any], Any], Any]


def _ndarray_validator(dims: Sequence[int], dtypes: Sequence[Type[np.generic]]) -> _Validator:
    def validator(inst: Any, attr: Attribute[Any], value: Any) -> None:
        if not isinstance(value, np.ndarray):
            raise TypeError("timestamps may only be of type np.ndarray")

        if not any(value.ndim == dim for dim in dims):
            raise ValueError(f"{attr.name} must be have dimension: {dims}")

        if not any(np.issubdtype(value.dtype, dtype) for dtype in dtypes):
            raise TypeError(f"{attr.name} must have dtype: {dtypes}")

    return validator


_ET = TypeVar("_ET")

_ST = TypeVar("_ST")
_DT = TypeVar("_DT", bound=np.generic)
_Array = np.ndarray[_ST, np.dtype[_DT]]
_1DArray = _Array[Tuple[int], _DT]
_2DArray = _Array[Tuple[int, int], _DT]

_numeric_types = (np.integer, np.floating)
_timestamp_validator = _ndarray_validator((1,), _numeric_types)
_trajectories_validator = _ndarray_validator((1, 2), _numeric_types)


class Evaluable(ABC):
    @abstractmethod
    def eval_using(self, spec: Specification) -> float:
        raise NotImplementedError()


Timestamps = Union[_1DArray[np.float_], _1DArray[np.int_]]
Trajectories = Union[_2DArray[np.float_], _2DArray[np.int_]]


@attrs(auto_attribs=True, frozen=True, init=False)
class SimulationResult(Generic[_ET], Evaluable):
    _trajectories: Trajectories = attrib(validator=_trajectories_validator, converter=np.array)
    timestamps: Timestamps = attrib(validator=_timestamp_validator, converter=np.array)
    extra: _ET

    @overload
    def __init__(self: SimulationResult[None], trajectories: Trajectories, timestamps: Timestamps):
        ...

    @overload
    def __init__(self, trajectories: Trajectories, timestamps: Timestamps, data: _ET):
        ...

    def __init__(self, trajectories: Trajectories, timestamps: Timestamps, data: _ET = None):
        self.__attrs_init__(trajectories, timestamps, data)  # type: ignore

    def eval_using(self, spec: Specification) -> float:
        return spec.evaluate(self.trajectories, self.timestamps)

    @property
    def trajectories(self) -> Trajectories:
        trajectories = np.atleast_2d(self._trajectories)

        if trajectories.shape[0] == self.timestamps.shape[0]:
            return trajectories.T
        elif trajectories.shape[1] == self.timestamps.shape[0]:
            return trajectories
        else:
            raise ValueError("No dimension of the trajectories matrix matches the timestamps len")


@attrs(auto_attribs=True, frozen=True, init=False)
class Falsification(Generic[_ET], Evaluable):
    extra: _ET

    @overload
    def __init__(self: Falsification[None]):
        ...

    @overload
    def __init__(self, data: _ET):
        ...

    def __init__(self, data: _ET = None):
        self.__attrs_init__(data)  # type: ignore

    def eval_using(self, spec: Specification) -> float:
        return -math.inf


StaticParameters = np.ndarray[Tuple[int], np.dtype[np.float_]]
SignalInterpolators = Sequence[SignalInterpolator]
ModelResult = Union[SimulationResult[_ET], Falsification[_ET]]


@attrs(auto_attribs=True, frozen=True)
class SimulationParams:
    static_parameters: StaticParameters
    interpolators: SignalInterpolators
    interval: Interval


class Model(ABC, Generic[_ET]):
    @abstractmethod
    def simulate(self, params: SimulationParams) -> ModelResult[_ET]:
        raise NotImplementedError()


SignalTimes = NDArray[np.float_]
SignalValues = NDArray[np.float_]
BlackboxFunc = Callable[[StaticParameters, SignalTimes, SignalValues], ModelResult[_ET]]


class Blackbox(Model[_ET]):
    def __init__(self, func: BlackboxFunc[_ET], sampling_interval: float = 0.1):
        self.func = func
        self.sampling_interval = sampling_interval

    def simulate(self, params: SimulationParams) -> ModelResult[_ET]:
        interval = params.interval
        duration = interval.upper - interval.lower
        point_count = math.floor(duration / self.sampling_interval)
        signal_times = np.linspace(start=interval.lower, stop=interval.upper, num=point_count)
        signal_traces = [
            interpolator.interpolate(signal_times) for interpolator in params.interpolators
        ]

        return self.func(params.static_parameters, signal_times, np.array(signal_traces))


Time = float
State = np.ndarray[Tuple[int], np.dtype[np.float_]]
IntegrationFn = Callable[[Time, State], State]
ODEFunc = Callable[[Time, State, SignalValues], State]


class _IntegrationFunc:
    def __init__(self, signals: SignalInterpolators, ode_func: ODEFunc):
        self.signals = signals
        self.func = ode_func

    def __call__(self, time: Time, state: State) -> State:
        signal_values = np.array([signal.interpolate(time) for signal in self.signals])
        return self.func(time, state, signal_values)


class ODE(Model[None]):
    def __init__(self, func: ODEFunc):
        self.func = func

    def simulate(self, params: SimulationParams) -> SimulationResult[None]:
        integration_fn = _IntegrationFunc(params.interpolators, self.func)
        integration = integrate.solve_ivp(
            integration_fn, params.interval.astuple(), params.static_parameters
        )

        return SimulationResult(integration.y, integration.t, None)


_BlackboxDecorator = Callable[[BlackboxFunc[_ET]], Blackbox[_ET]]


@overload
def blackbox(*, sampling_interval: float = ...) -> Callable[[BlackboxFunc[_ET]], Blackbox[_ET]]:
    ...


@overload
def blackbox(_func: BlackboxFunc[_ET]) -> Blackbox[_ET]:
    ...


def blackbox(
    _func: Optional[BlackboxFunc[_ET]] = None, *, sampling_interval: float = 0.1
) -> Union[Blackbox[_ET], _BlackboxDecorator[_ET]]:
    """Decorate a function as a blackbox model.

    This decorator can be used with or without arguments.

    Args:
        func: The function to wrap as a blackbox
        *: Variable length argument list
        sampling_interval: The time interval to use when sampling the signal interpolators

    Returns:
        A blackbox model
    """

    def decorator(func: BlackboxFunc[_ET]) -> Blackbox[_ET]:
        return Blackbox(func, sampling_interval)

    if _func is not None:
        return decorator(_func)
    else:
        return decorator


_ODEDecorator = Callable[[ODEFunc], ODE]


@overload
def ode() -> _ODEDecorator:
    ...


@overload
def ode(_func: ODEFunc) -> ODE:
    ...


def ode(_func: Optional[ODEFunc] = None) -> Union[_ODEDecorator, ODE]:
    def decorator(func: ODEFunc) -> ODE:
        return ODE(func)

    if _func is not None:
        return decorator(_func)
    else:
        return decorator

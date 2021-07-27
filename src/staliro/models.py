from __future__ import annotations

import math
import sys
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, Union, Optional, Type, TYPE_CHECKING

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


_RealVector = Union[NDArray[np.float_], NDArray[np.int_]]
_T = TypeVar("_T")
_numeric_types = (np.integer, np.floating)
_timestamp_validator = _ndarray_validator((1,), _numeric_types)
_trajectories_validator = _ndarray_validator((1, 2), _numeric_types)


class Evaluable(ABC):
    @abstractmethod
    def eval_using(self, spec: Specification) -> float:
        raise NotImplementedError()


@attrs(auto_attribs=True, frozen=True, init=False)
class SimulationResult(Generic[_T], Evaluable):
    _trajectories: _RealVector = attrib(validator=_trajectories_validator, converter=np.array)
    timestamps: _RealVector = attrib(validator=_timestamp_validator, converter=np.array)
    data: _T

    @overload
    def __init__(self: SimulationResult[None], trajectories: _RealVector, timestamps: _RealVector):
        ...

    @overload
    def __init__(self, trajectories: _RealVector, timestamps: _RealVector, data: _T):
        ...

    def __init__(self, trajectories: _RealVector, timestamps: _RealVector, data: _T = None):
        self.__attrs_init__(trajectories, timestamps, data)  # type: ignore

    def eval_using(self, spec: Specification) -> float:
        return spec.evaluate(self.trajectories, self.timestamps)

    @property
    def trajectories(self) -> _RealVector:
        trajectories = np.atleast_2d(self._trajectories)

        if trajectories.shape[0] == self.timestamps.shape[0]:
            return trajectories.T
        elif trajectories.shape[1] == self.timestamps.shape[0]:
            return trajectories
        else:
            raise ValueError("No dimension of the trajectories matrix matches the timestamps len")


@attrs(auto_attribs=True, frozen=True, init=False)
class Falsification(Generic[_T], Evaluable):
    data: _T

    @overload
    def __init__(self: Falsification[None]):
        ...

    @overload
    def __init__(self, data: _T):
        ...

    def __init__(self, data: _T = None):
        self.__attrs_init__(data)  # type: ignore

    def eval_using(self, spec: Specification) -> float:
        return -math.inf


StaticParameters = _RealVector
SignalInterpolators = Sequence[SignalInterpolator]
ModelResult = Union[SimulationResult[_T], Falsification[_T]]


@attrs(auto_attribs=True, frozen=True)
class SimulationParams:
    static_parameters: StaticParameters
    interpolators: SignalInterpolators
    interval: Interval


class Model(ABC, Generic[_T]):
    @abstractmethod
    def simulate(self, params: SimulationParams) -> ModelResult[_T]:
        raise NotImplementedError()


SignalTimes = NDArray[np.float_]
SignalValues = NDArray[np.float_]
Timestamps = Union[_RealVector, Sequence[float], Sequence[int]]
Trajectories = Union[_RealVector, Sequence[Sequence[float]], Sequence[Sequence[int]]]
BlackboxFunc = Callable[[StaticParameters, SignalTimes, SignalValues], ModelResult[_T]]


class Blackbox(Model[_T]):
    def __init__(self, func: BlackboxFunc[_T], sampling_interval: float = 0.1):
        self.func = func
        self.sampling_interval = sampling_interval

    def simulate(self, params: SimulationParams) -> ModelResult[_T]:
        interval = params.interval
        duration = interval.upper - interval.lower
        point_count = math.floor(duration / self.sampling_interval)
        signal_times = np.linspace(start=interval.lower, stop=interval.upper, num=point_count)
        signal_traces = [
            interpolator.interpolate(signal_times) for interpolator in params.interpolators
        ]

        return self.func(params.static_parameters, signal_times, np.array(signal_traces))


Time = float
State = _RealVector
IntegrationFn = Callable[[float, _RealVector], _RealVector]
ODEResult = Union[_RealVector, Sequence[float], Sequence[int]]
ODEFunc = Callable[[Time, State, SignalValues], ODEResult]


def _make_integration_fn(signals: SignalInterpolators, func: ODEFunc) -> IntegrationFn:
    def integration_fn(time: float, state: State) -> State:
        signal_values = [signal.interpolate(time) for signal in signals]
        result = func(time, state, np.array(signal_values))
        return np.array(result)

    return integration_fn


class ODE(Model[None]):
    def __init__(self, func: ODEFunc):
        self.func = func

    def simulate(self, params: SimulationParams) -> SimulationResult[None]:
        integration_fn = _make_integration_fn(params.interpolators, self.func)
        integration = integrate.solve_ivp(
            integration_fn, params.interval.astuple(), params.static_parameters
        )

        return SimulationResult(integration.y, integration.t, None)


_BlackboxDecorator = Callable[[BlackboxFunc[_T]], Blackbox[_T]]


@overload
def blackbox(*, sampling_interval: float = ...) -> Callable[[BlackboxFunc[_T]], Blackbox[_T]]:
    ...


@overload
def blackbox(_func: BlackboxFunc[_T]) -> Blackbox[_T]:
    ...


def blackbox(
    _func: Optional[BlackboxFunc[_T]] = None, *, sampling_interval: float = 0.1
) -> Union[Blackbox[_T], _BlackboxDecorator[_T]]:
    """Decorate a function as a blackbox model.

    This decorator can be used with or without arguments.

    Args:
        func: The function to wrap as a blackbox
        *: Variable length argument list
        sampling_interval: The time interval to use when sampling the signal interpolators

    Returns:
        A blackbox model
    """

    def decorator(func: BlackboxFunc[_T]) -> Blackbox[_T]:
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

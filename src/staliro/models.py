from __future__ import annotations

import math
import sys
from typing import Any, Generic, TypeVar, Union, Optional, Type

if sys.version_info >= (3, 9):
    from collections.abc import Sequence, Callable
else:
    from typing import Sequence, Callable

import numpy as np
from attr import Attribute, attrs, attrib
from numpy.typing import NDArray
from scipy import integrate
from typing_extensions import Protocol, runtime_checkable, overload

from .options import Interval
from .signals import SignalInterpolator

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


@attrs(auto_attribs=True, frozen=True)
class SimulationResult(Generic[_T]):
    _trajectories: _RealVector = attrib(validator=_trajectories_validator, converter=np.ndarray)
    timestamps: _RealVector = attrib(validator=_timestamp_validator, converter=np.ndarray)
    extra: _T

    def __attrs_post_init__(self) -> None:
        if not any(dim == self.timestamps.shape[0] for dim in self._trajectories.shape):
            raise ValueError("expected one trajectories dimension to match timestamps length")

    @property
    def trajectories(self) -> _RealVector:
        _trajectories = np.atleast_2d(self._trajectories)

        if _trajectories.shape[0] == self.timestamps.shape[0]:
            return _trajectories.T

        return _trajectories


class Falsification:
    pass


StaticParameters = _RealVector
SignalInterpolators = Sequence[SignalInterpolator]

ModelResult = Union[SimulationResult[_T], Falsification]


@attrs()
class SimulationParams:
    static_parameters: StaticParameters
    interpolators: SignalInterpolators
    interval: Interval


@runtime_checkable
class Model(Protocol[_T]):
    def simulate(self, __params: SimulationParams) -> ModelResult[_T]:
        ...


SignalTimes = NDArray[np.float_]
SignalValues = NDArray[np.float_]
Timestamps = Union[_RealVector, Sequence[float], Sequence[int]]
Trajectories = Union[_RealVector, Sequence[Sequence[float]], Sequence[Sequence[int]]]
BlackboxResult = Union[SimulationResult[_T], Falsification]
BlackboxFunc = Callable[[StaticParameters, SignalTimes, SignalValues], BlackboxResult[_T]]


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


class ODE(Model):
    def __init__(self, func: ODEFunc):
        self.func = func

    def simulate(
        self,
        static_params: StaticParameters,
        interpolators: SignalInterpolators,
        interval: Interval,
    ) -> ModelResult:
        integration_fn = _make_integration_fn(interpolators, self.func)
        integration = integrate.solve_ivp(integration_fn, interval.astuple(), static_params)

        return SimulationResult(integration.y, integration.t)


_BlackboxDecorator = Callable[[BlackboxFunc], Blackbox]


@overload
def blackbox(*, sampling_interval: float = ...) -> _BlackboxDecorator:
    ...


@overload
def blackbox(_func: BlackboxFunc) -> Blackbox:
    ...


def blackbox(
    _func: Optional[BlackboxFunc] = None, *, sampling_interval: float = 0.1
) -> Union[Blackbox, _BlackboxDecorator]:
    """Decorate a function as a blackbox model.

    This decorator can be used with or without arguments.

    Args:
        func: The function to wrap as a blackbox
        *: Variable length argument list
        sampling_interval: The time interval to use when sampling the signal interpolators

    Returns:
        A blackbox model
    """

    def decorator(func: BlackboxFunc) -> Blackbox:
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

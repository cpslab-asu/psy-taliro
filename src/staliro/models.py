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


_ET = TypeVar("_ET")

_numeric_types = (np.integer, np.floating)
_timestamp_validator = _ndarray_validator((1,), _numeric_types)
_trajectories_validator = _ndarray_validator((1, 2), _numeric_types)


class Evaluable(ABC):
    @abstractmethod
    def eval_using(self, spec: Specification) -> float:
        raise NotImplementedError()


Timestamps = Union[NDArray[np.float_], NDArray[np.int_]]
Trajectories = Union[NDArray[np.float_], NDArray[np.int_]]


@attrs(auto_attribs=True, frozen=True, init=False)
class SimulationResult(Generic[_ET], Evaluable):
    """Data class that represents a successful simulation.

    A successful simulation produces a vector of timestamps and a matrix of state values. The state
    value matrix must be 2-dimensional and one of the dimensions must be equal to the length of the
    timestamps vector.

    Args:
        trajectories: Array of state values
        timestamps: Array of time values corresponding to each set of state values
        extra: User-defined data related to the simulation

    Attributes:
        timestamps: Vector of time values that correspond to the states in the trajectories matrix
        extra: User-defined data
    """

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
        """The time-varying state matrix.

        The matrix is returned oriented so that the axis which matches the length of the timestamps
        vector is the columns of the matrix. This implies that each state value over time is
        available as a row.

        Given: [t1, t2, t3...tn]
        Matrix: [[s11, s12, s13...s1t],
                 [s21, s22, s21...s2t]...]
        """

        trajectories = np.atleast_2d(self._trajectories)

        if trajectories.shape[0] == self.timestamps.shape[0]:
            return trajectories.T
        elif trajectories.shape[1] == self.timestamps.shape[0]:
            return trajectories
        else:
            raise ValueError("No dimension of the trajectories matrix matches the timestamps len")


@attrs(auto_attribs=True, frozen=True, init=False)
class Falsification(Generic[_ET], Evaluable):
    """Data class that represents a falsification of the requirement.

    Some use-cases require manual falsification outside of the specification. This class always
    returns a cost of minus infinity.

    Args:
        extra: User-defined data

    Attributes:
        extra: User-defined data
    """

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


StaticParameters = NDArray[np.float_]
SignalInterpolators = Sequence[SignalInterpolator]
ModelResult = Union[SimulationResult[_ET], Falsification[_ET]]


@attrs(auto_attribs=True, frozen=True)
class SimulationParams:
    """Data class that contains the required data for a simulation.

    Attributes:
        static_parameters: Time-invariant system inputs (often used as initial conditions).
        interpolators: Time-varying inputs to the system represented as interpolated functions.
        interval: The time interval over which the simulation should run.
    """

    static_parameters: StaticParameters
    interpolators: SignalInterpolators
    interval: Interval


class Model(ABC, Generic[_ET]):
    """Representation of a system under test."""

    @abstractmethod
    def simulate(self, params: SimulationParams) -> ModelResult[_ET]:
        """Given a set of time-invariant/varying inputs, simulate a system over an interval.

        Args:
            params: SimulationParams class containing the time-invariant/varying inputs to the
                    system and the interval

        Returns:
            An instance of SimulationResult indicating success, or an instance of Falsification
            indicating an manual falsification.
        """

        raise NotImplementedError()


SignalTimes = NDArray[np.float_]
SignalValues = NDArray[np.float_]
BlackboxFunc = Callable[[StaticParameters, SignalTimes, SignalValues], ModelResult[_ET]]


class Blackbox(Model[_ET]):
    """General system model which does not make assumptions about the underlying system.

    Attributes:
        func: User-defined function which is given the static parameters, a vector of time values,
              and a matrix of interpolated signal values and returns a SimulationResult or
              Falsification
        sampling_interval: Time-step to use for interpolating signal values over the simulation
                           interval
    """

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
State = NDArray[np.float_]
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
    """Model which assumes the underlying system is modeled by an Ordinary Differential Equation.

    Attributes:
        func: User-defined function which is given a time value, a state, and a vector of signal
              values and returns a new state.
    """

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
    """Decorate a function as an ODE model.

    This decorator can be used with or without arguments.

    Args:
        _func: The function to wrap as an ODE model

    Returns:
        An ODE model
    """

    def decorator(func: ODEFunc) -> ODE:
        return ODE(func)

    if _func is not None:
        return decorator(_func)
    else:
        return decorator

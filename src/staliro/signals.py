from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from typing import Tuple, Union, List

if sys.version_info >= (3, 9):
    from collections.abc import Sequence, Callable
else:
    from typing import Sequence, Callable


import numpy as np
import scipy as sp
import scipy.interpolate as spi
from numpy.typing import NDArray
from typing_extensions import Protocol, runtime_checkable, overload

_RealVector = Union[NDArray[np.int_], NDArray[np.float_]]


class SignalInterpolator(Protocol):
    """Interface for callable that provides interpolated signal values at given time t.

    A signal interpolator should provide an interpolated value for the signal at any time t within
    the simulation time interval. All signal interpolators should return their value synchonously.
    """

    @overload
    def interpolate(self, __value: float) -> float:
        ...

    @overload
    def interpolate(self, __value: Sequence[float]) -> Sequence[float]:
        ...


class ScipyInterpolator(Protocol):
    @overload
    def __call__(self, x: float) -> float:
        ...

    @overload
    def __call__(self, x: Sequence[float]) -> NDArray[np.float_]:
        ...


class ScipyWrapper(ABC, SignalInterpolator):
    constructor: Callable[[Sequence[float], Sequence[float]], ScipyInterpolator]

    def __init__(self, x_values: Sequence[float], y_values: Sequence[float]):
        self.interpolator = self.constructor(x_values, y_values)

    @overload
    def interpolate(self, x: float) -> float:
        ...

    @overload
    def interpolate(self, x: Sequence[float]) -> Sequence[float]:
        ...

    def interpolate(self, x: Union[float, Sequence[float]]) -> Union[float, Sequence[float]]:
        if isinstance(x, float):
            return self.interpolator(x)
        elif isinstance(x, Sequence):
            return list(self.interpolator(x))
        else:
            raise TypeError()


class PchipInterpolator(ScipyWrapper):
    constructor = spi.PchipInterpolator


class PiecewiseLinearInterpolator(SignalInterpolator):
    constructor = spi.interp1d


class PiecewiseConstantInterpolator(SignalInterpolator):
    constructor = lambda x, y: spi.interp1d(x, y, kind="zero", fill_value="extrapolate")

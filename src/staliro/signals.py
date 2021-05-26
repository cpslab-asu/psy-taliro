from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from typing import Tuple, Sequence, Union

if sys.version_info >= (3, 8):
    from typing import Protocol, runtime_checkable, overload
else:
    from typing_extensions import Protocol, runtime_checkable, overload

from numpy import ndarray, linspace
from scipy.interpolate import PchipInterpolator, interp1d


class SignalInterpolator(Protocol):
    """Interface for callable that provides interpolated signal values at given time t.

    A signal interpolator should provide an interpolated value for the signal at any time t within
    the simulation time interval. All signal interpolators should return their value synchonously.
    """

    @overload
    def interpolate(self, __value: float) -> float:
        ...

    @overload
    def interpolate(
        self, __value: Union[Sequence[float], ndarray]
    ) -> Union[Sequence[float], ndarray]:
        ...


@runtime_checkable
class InterpolatorFactory(Protocol):
    """Interface for factory function to return signal interpolators."""

    def create(self, interval: Tuple[float, float], y_values: ndarray) -> SignalInterpolator:
        ...


class _ScipyFactory(ABC, InterpolatorFactory):
    """Common base class for all interpolator generators wrapping scipy interpolators."""

    @abstractmethod
    def _create(self, x_values: ndarray, y_values: ndarray) -> SignalInterpolator:
        raise NotImplementedError()

    def _x_values(self, interval: Tuple[float, float], size: float) -> ndarray:
        return linspace(interval[0], interval[1], size, endpoint=True)  # type: ignore

    def create(self, interval: Tuple[float, float], y_values: ndarray) -> SignalInterpolator:
        x_values = self._x_values(interval, y_values.size)
        return self._create(x_values, y_values)


class PchipWrapper(SignalInterpolator):
    def __init__(self, x_values: ndarray, y_values: ndarray):
        self.interpolator = PchipInterpolator(x_values, y_values)

    @overload
    def interpolate(self, x: float) -> float:
        ...

    @overload
    def interpolate(self, x: Union[Sequence[float], ndarray]) -> ndarray:
        ...

    def interpolate(self, x: Union[float, ndarray, Sequence[float]]) -> Union[float, ndarray]:
        return self.interpolator(x)


class PchipFactory(_ScipyFactory):
    """Factory to return pchip interpolators."""

    def _create(self, x_values: ndarray, y_values: ndarray) -> PchipWrapper:
        return PchipWrapper(x_values, y_values)


class LinearWrapper(SignalInterpolator):
    def __init__(self, x_values: ndarray, y_values: ndarray):
        self.interpolater = interp1d(x_values, y_values)

    @overload
    def interpolate(self, x: float) -> float:
        ...

    @overload
    def interpolate(self, x: Union[Sequence[float], ndarray]) -> ndarray:
        ...

    def interpolate(self, x: Union[float, ndarray, Sequence[float]]) -> Union[float, ndarray]:
        return self.interpolater(x)


class LinearFactory(_ScipyFactory):
    """Factory to create piecewise linear interpolators."""

    def _create(self, x_values: ndarray, y_values: ndarray) -> LinearWrapper:
        return LinearWrapper(x_values, y_values)


class ConstantWrapper(SignalInterpolator):
    def __init__(self, x_values: ndarray, y_values: ndarray):
        self.interpolater = interp1d(x_values, y_values, kind="zero", fill_value="extrapolate")

    @overload
    def interpolate(self, x: float) -> float:
        ...

    @overload
    def interpolate(self, x: Union[Sequence[float], ndarray]) -> ndarray:
        ...

    def interpolate(self, x: Union[float, ndarray, Sequence[float]]) -> Union[float, ndarray]:
        return self.interpolater(x)


class ConstantFactory(_ScipyFactory):
    """Factory to create piecewise constant interpolators."""

    def _create(self, x_values: ndarray, y_values: ndarray) -> ConstantWrapper:
        return ConstantWrapper(x_values, y_values)

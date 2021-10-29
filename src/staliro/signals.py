from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Sequence

import numpy as np
from numpy.typing import NDArray
from scipy.interpolate import PchipInterpolator, interp1d
from typing_extensions import Protocol, overload

from .core.signal import Signal


class ScipyInterpolator(Protocol):
    @overload
    def __call__(self, x: float) -> float:
        ...

    @overload
    def __call__(self, x: Sequence[float]) -> NDArray[np.float_]:
        ...


class ScipySignal(Signal, ABC):
    interpolator: ScipyInterpolator

    @abstractmethod
    def __init__(self, xs: Sequence[float], ys: Sequence[float]):
        ...

    def at_time(self, t: float) -> float:
        return self.interpolator(t)

    def at_times(self, ts: Sequence[float]) -> List[float]:
        return self.interpolator(ts).tolist()  # type: ignore


class Pchip(ScipySignal):
    def __init__(self, xs: Sequence[float], ys: Sequence[float]):
        self.interpolator = PchipInterpolator(xs, ys)


class PiecewiseLinear(ScipySignal):
    def __init__(self, xs: Sequence[float], ys: Sequence[float]):
        self.interpolator = interp1d(xs, ys)


class PiecewiseConstant(ScipySignal):
    def __init__(self, xs: Sequence[float], ys: Sequence[float]):
        self.interpolator = interp1d(xs, ys, kind="zero", fill_value="extrapolate")

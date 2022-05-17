from __future__ import annotations

from typing import List, Sequence, cast

from scipy.interpolate import PchipInterpolator, interp1d

from .core.signal import Signal


class Pchip(Signal):
    def __init__(self, interp: PchipInterpolator):
        self.interp = interp

    def at_time(self, t: float) -> float:
        return float(self.interp(t))

    def at_times(self, ts: Sequence[float]) -> List[float]:
        return cast(List[float], self.interp(ts))


def pchip(times: Sequence[float], signal_values: Sequence[float]) -> Pchip:
    return Pchip(PchipInterpolator(times, signal_values))


class PiecewiseLinear(Signal):
    def __init__(self, interp: interp1d):
        self.interp = interp

    def at_time(self, t: float) -> float:
        return float(self.interp(t))

    def at_times(self, ts: Sequence[float]) -> List[float]:
        return cast(List[float], self.interp(ts))


def piecewise_linear(times: Sequence[float], signal_values: Sequence[float]) -> PiecewiseLinear:
    return PiecewiseLinear(interp1d(times, signal_values))


class PiecewiseConstant(Signal):
    def __init__(self, interp: interp1d):
        self.interp = interp

    def at_time(self, t: float) -> float:
        return float(self.interp(t))

    def at_times(self, ts: Sequence[float]) -> List[float]:
        return cast(List[float], self.interp(ts))


def piecewise_constant(times: Sequence[float], signal_values: Sequence[float]) -> PiecewiseConstant:
    return PiecewiseConstant(interp1d(times, signal_values, kind="zero", fill_value="extrapolate"))

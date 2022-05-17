from __future__ import annotations

from typing import List, Sequence, cast

import numpy as np
from scipy.interpolate import PchipInterpolator, interp1d

from .core.signal import Signal, SignalFactory


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


class Delayed(Signal):
    def __init__(self, signal: Signal, cutoff: int):
        self.signal = signal
        self.cutoff = cutoff

    def at_time(self, t: float) -> float:
        if t < self.cutoff:
            return 0.0

        return self.signal.at_time(t)

    def at_times(self, ts: Sequence[float]) -> List[float]:
        return [self.at_time(t) for t in ts]


def delayed(signal_factory: SignalFactory, *, delay: int) -> SignalFactory:
    def factory(times: Sequence[float], signal_values: Sequence[float]) -> Signal:
        stop_time = max(times)
        new_times = np.linspace(
            start=delay, stop=stop_time, num=len(signal_values), dtype=np.float64
        )
        signal = signal_factory(new_times.tolist(), signal_values)

        return Delayed(signal, delay)

    return factory

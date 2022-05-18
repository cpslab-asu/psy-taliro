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
        return cast(List[float], self.interp(ts).tolist())


def pchip(times: Sequence[float], signal_values: Sequence[float]) -> Pchip:
    return Pchip(PchipInterpolator(times, signal_values))


class PiecewiseLinear(Signal):
    def __init__(self, interp: interp1d):
        self.interp = interp

    def at_time(self, t: float) -> float:
        return float(self.interp(t))

    def at_times(self, ts: Sequence[float]) -> List[float]:
        return cast(List[float], self.interp(ts).tolist())


def piecewise_linear(times: Sequence[float], signal_values: Sequence[float]) -> PiecewiseLinear:
    return PiecewiseLinear(interp1d(times, signal_values))


class PiecewiseConstant(Signal):
    def __init__(self, interp: interp1d):
        self.interp = interp

    def at_time(self, t: float) -> float:
        return float(self.interp(t))

    def at_times(self, ts: Sequence[float]) -> List[float]:
        return cast(List[float], self.interp(ts).tolist())


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


class Sequenced(Signal):
    def __init__(self, s1: Signal, s2: Signal, t_switch: int):
        self.s1 = s1
        self.s2 = s2
        self.t_switch = t_switch

    def at_time(self, t: float) -> float:
        return self.s1.at_time(t) if t < self.t_switch else self.s2.at_time(t)

    def at_times(self, ts: Sequence[float]) -> List[float]:
        return [self.at_time(t) for t in ts]


def sequenced(factory1: SignalFactory, factory2: SignalFactory, *, t_switch: int) -> SignalFactory:
    def factory(times: Sequence[float], signal_values: Sequence[float]) -> Signal:
        signal1_indices = [i for i, t in enumerate(times) if t < t_switch]
        signal2_indices = [i for i, t in enumerate(times) if t >= t_switch]
        signal1 = factory1(
            [times[i] for i in signal1_indices], [signal_values[i] for i in signal1_indices]
        )
        signal2 = factory2(
            [times[i] for i in signal2_indices], [signal_values[i] for i in signal2_indices]
        )

        return Sequenced(signal1, signal2, t_switch)

    return factory

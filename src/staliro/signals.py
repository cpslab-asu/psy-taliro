from __future__ import annotations

from math import cos
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


class Piecewise(Signal):
    def __init__(self, interp: interp1d):
        self.interp = interp

    def at_time(self, t: float) -> float:
        return float(self.interp(t))

    def at_times(self, ts: Sequence[float]) -> List[float]:
        return cast(List[float], self.interp(ts).tolist())


def piecewise_linear(times: Sequence[float], signal_values: Sequence[float]) -> Piecewise:
    return Piecewise(interp1d(times, signal_values))


def piecewise_constant(times: Sequence[float], signal_values: Sequence[float]) -> Piecewise:
    return Piecewise(interp1d(times, signal_values, kind="zero", fill_value="extrapolate"))


class Delayed(Signal):
    def __init__(self, signal: Signal, cutoff: int):
        self.signal = signal
        self.cutoff = cutoff

    def at_time(self, t: float) -> float:
        if t < self.cutoff:
            return 0.0

        return self.signal.at_time(t)


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


class Harmonic(Signal):
    class Component:
        def __init__(self, amplitude: float, frequency: float, phase: float):
            self.theta = amplitude
            self.omega = frequency
            self.phi = phase

        def at_time(self, time: float) -> float:
            return self.theta * cos(self.omega * time - self.phi)

    def __init__(self, bias: float, components: Sequence[Harmonic.Component]):
        self.bias = bias
        self.components = tuple(components)

    def at_time(self, time: float) -> float:
        return self.bias + sum(component.at_time(time) for component in self.components)


def harmonic(_: Sequence[float], values: Sequence[float]) -> Harmonic:
    if len(values[1:]) % 3 != 0:
        raise RuntimeError("Insufficient number of values to generate a harmonic signal")

    bias = values[0]
    component_params = [(values[i], values[i + 1], values[i + 2]) for i in range(1, len(values), 3)]
    components = [Harmonic.Component(amp, freq, phase) for amp, freq, phase in component_params]

    return Harmonic(bias, components)


class Clamped(Signal):
    def __init__(self, s: Signal, lo: float, hi: float):
        self._signal = s
        self._lo = lo
        self._hi = hi

    def at_time(self, time: float) -> float:
        return min(self._hi, max(self._lo, self._signal.at_time(time)))


def clamped(factory: SignalFactory, *, lo: float, hi: float) -> SignalFactory:
    def _factory(times: Sequence[float], values: Sequence[float]) -> Clamped:
        return Clamped(factory(times, values), lo, hi)

    return _factory

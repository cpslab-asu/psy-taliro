from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from math import cos
from typing import Protocol, cast

import numpy as np
from scipy.interpolate import PchipInterpolator, interp1d


class Signal(ABC):
    """Representation of a time-varying input to a system."""

    @abstractmethod
    def at_time(self, time: float) -> float:
        """Get the value of the signal at the specified time."""

        raise NotImplementedError()

    def at_times(self, times: Sequence[float]) -> list[float]:
        """Get the value of the signal at each specified time."""

        return [self.at_time(time) for time in times]



class SignalFactory(Protocol):
    def __call__(self, __times: Iterable[float], __values: Iterable[float]) -> Signal:
        ...


class Pchip(Signal):
    def __init__(self, interp: PchipInterpolator):
        self.interp = interp

    def at_time(self, t: float) -> float:
        return float(self.interp(t))

    def at_times(self, ts: Sequence[float]) -> list[float]:
        return cast(list[float], self.interp(ts).tolist())


def pchip(times: Iterable[float], values: Iterable[float]) -> Pchip:
    return Pchip(PchipInterpolator(list(times), list(values)))


class Piecewise(Signal):
    def __init__(self, interp: interp1d):
        self.interp = interp

    def at_time(self, t: float) -> float:
        return float(self.interp(t))

    def at_times(self, ts: Sequence[float]) -> list[float]:
        return cast(list[float], self.interp(ts).tolist())


def piecewise_linear(times: Iterable[float], values: Iterable[float]) -> Piecewise:
    return Piecewise(interp1d(list(times), list(values)))


def piecewise_constant(times: Iterable[float], values: Iterable[float]) -> Piecewise:
    return Piecewise(interp1d(list(times), list(values), kind="zero", fill_value="extrapolate"))


class Delayed(Signal):
    def __init__(self, signal: Signal, cutoff: int):
        self.signal = signal
        self.cutoff = cutoff

    def at_time(self, t: float) -> float:
        if t < self.cutoff:
            return 0.0

        return self.signal.at_time(t)


def delayed(signal_factory: SignalFactory, *, delay: int) -> SignalFactory:
    def _factory(times: Iterable[float], values: Iterable[float]) -> Signal:
        values = list(values)
        stop_time = max(times)
        new_times = np.linspace(start=delay, stop=stop_time, num=len(values), dtype=float)
        signal = signal_factory(new_times.tolist(), values)

        return Delayed(signal, delay)

    return _factory


class Sequenced(Signal):
    def __init__(self, s1: Signal, s2: Signal, t_switch: int):
        self.s1 = s1
        self.s2 = s2
        self.t_switch = t_switch

    def at_time(self, t: float) -> float:
        return self.s1.at_time(t) if t < self.t_switch else self.s2.at_time(t)


def sequenced(factory1: SignalFactory, factory2: SignalFactory, *, t_switch: int) -> SignalFactory:
    def _factory(times: Iterable[float], values: Iterable[float]) -> Signal:
        times_values = zip(times, values)
        s1_data = [(time, value) for time, value in times_values if time < t_switch]
        s1 = factory1((time for time, _ in s1_data), (value for _, value in s1_data))

        s2_data = [(time, value) for time, value in times_values if time >= t_switch]
        s2 = factory2((time for time, _ in s2_data), (value for _, value in s2_data))

        return Sequenced(s1, s2, t_switch)

    return _factory


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


def harmonic(_: Iterable[float], values: Iterable[float]) -> Harmonic:
    values = list(values)

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
    def _factory(times: Iterable[float], values: Iterable[float]) -> Clamped:
        return Clamped(factory(times, values), lo, hi)

    return _factory

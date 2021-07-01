from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from time import perf_counter
from typing import Union

from .models import (
    Model,
    StaticParameters,
    SignalInterpolators,
    Interval,
    SimulationResult,
    Falsification,
)
from .specification import Specification


class TimedModel(Model):
    def __init__(self, model: Model):
        self.model = model
        self.times: list[float] = []

    def simulate(
        self,
        static_params: StaticParameters,
        interpolators: SignalInterpolators,
        interval: Interval,
    ) -> Union[SimulationResult, Falsification]:
        t_start = perf_counter()
        result = self.model.simulate(static_params, interpolators, interval)
        t_stop = perf_counter()

        self.times.append(t_stop - t_start)

        return result


class TimedSpecification(Specification):
    def __init__(self, specification: Specification):
        self.spec = specification
        self.times: list[float] = []

    def evaluate(self, result: SimulationResult) -> float:
        t_start = perf_counter()
        cost = self.spec.evaluate(result)
        t_stop = perf_counter()

        self.times.append(t_stop - t_start)

        return cost


@dataclass()
class TimeStats:
    _times: list[float]

    @property
    def total(self) -> float:
        return sum(self._times)

    @property
    def average(self) -> float:
        return mean(self._times)

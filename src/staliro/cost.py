from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from multiprocessing import Pool
from typing import Generic, List, Tuple, TypeVar, Union

if sys.version_info >= (3, 9):
    from collections.abc import Sequence, Iterable, Callable
else:
    from typing import Sequence, Iterable, Callable

import numpy as np

from .models import Model, SimulationParams, StaticParameters, SignalInterpolator
from .options import Options
from .specification import Specification

_ET = TypeVar("_ET")
_AT = TypeVar("_AT", bound=np.generic)
_1DArray = np.ndarray[Tuple[int], np.dtype[_AT]]
_2DArray = np.ndarray[Tuple[int, int], np.dtype[_AT]]

Sample = Union[Sequence[float], _1DArray[np.int_], _1DArray[np.float_]]
Samples = Union[
    Sequence[Sequence[float]],
    Sequence[_1DArray[np.int_]],
    Sequence[_1DArray[np.float_]],
    _2DArray[np.int_],
    _2DArray[np.float_],
]

SpecificationFactory = Callable[[Sample], Specification]
SpecificationOrFactory = Union[Specification, SpecificationFactory]


def _static_parameters(sample: Sample, options: Options) -> StaticParameters:
    return sample[0 : len(options.static_parameters)]  # type: ignore


def _signal_interpolators(sample: Sample, options: Options) -> List[SignalInterpolator]:
    start = len(options.static_parameters)
    interpolators: List[SignalInterpolator] = []

    for signal in options.signals:
        factory = signal.factory
        end = start + signal.control_points
        interpolators.append(factory.create(signal.interval.astuple(), sample[start:end]))  # type: ignore
        start = end

    return interpolators


def _specification(sample: Sample, specification: SpecificationOrFactory) -> Specification:
    if callable(specification):
        return specification(sample)

    return specification


def _simulation_params(sample: Sample, options: Options) -> SimulationParams:
    static_params = _static_parameters(sample, options)
    interpolators = _signal_interpolators(sample, options)

    return SimulationParams(static_params, interpolators, options.interval)


@dataclass(frozen=True)
class TimingData:
    model: float
    specification: float

    @property
    def total(self) -> float:
        return self.model + self.specification


@dataclass(frozen=True)
class Evaluation(Generic[_ET]):
    cost: float
    sample: Sample
    extra: _ET
    timing: TimingData


@dataclass(frozen=True)
class Thunk(Generic[_ET]):
    sample: Sample
    model: Model[_ET]
    specification: Specification
    options: Options

    def evaluate(self) -> Evaluation[_ET]:
        simulation_params = _simulation_params(self.sample, self.options)
        model_start = time.perf_counter()
        model_result = self.model.simulate(simulation_params)
        model_stop = time.perf_counter()

        spec_start = time.perf_counter()
        cost = model_result.eval_using(self.specification)
        spec_stop = time.perf_counter()
        timing_data = TimingData(model_stop - model_start, spec_stop - spec_start)

        return Evaluation(cost, self.sample, model_result.extra, timing_data)


def _evaluate(thunk: Thunk[_ET]) -> Evaluation[_ET]:
    return thunk.evaluate()


class CostFn(Generic[_ET]):
    def __init__(self, model: Model[_ET], specification: SpecificationOrFactory, options: Options):
        self.model = model
        self.specification = specification
        self.options = options
        self.history: List[Evaluation[_ET]] = []

    def _thunks(self, samples: Samples) -> Iterable[Thunk[_ET]]:
        for sample in samples:
            specification = _specification(sample, self.specification)
            yield Thunk(sample, self.model, specification, self.options)

    def eval_sample(self, sample: Sample) -> float:
        specification = _specification(sample, self.specification)
        thunk = Thunk(sample, self.model, specification, self.options)
        evaluation = thunk.evaluate()

        self.history.append(evaluation)

        return evaluation.cost

    def eval_samples(self, samples: Samples) -> List[float]:
        return [self.eval_sample(sample) for sample in samples]

    def eval_samples_parallel(self, samples: Samples, processes: int) -> List[float]:
        with Pool(processes=processes) as pool:
            evaluations: List[Evaluation[_ET]] = pool.map(_evaluate, self._thunks(samples))

        costs = [evaluation.cost for evaluation in evaluations]

        self.history.extend(evaluations)

        return costs

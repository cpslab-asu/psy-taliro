from __future__ import annotations

import sys
import time
from collections import deque
from typing import Any, Generator, Generic, List, Tuple, TypeVar, Union, Deque

if sys.version_info >= (3, 9):
    from collections.abc import Callable
else:
    from typing import Callable

from numpy.random import default_rng
from typing_extensions import overload, Literal

from .models import (
    Falsification,
    Model,
    ModelResult,
    SimulationParams,
    SimulationResult,
    StaticParameters,
    SignalInterpolators,
)
from .optimizers import Optimizer, Sample, OptimizationFn, OptimizationParams
from .options import Options
from .signals import SignalInterpolator
from .specification import Specification, SpecificationFactory
from .results import Iteration, Result, TimedIteration, Run, TimedRun, TimedResult

_RT = TypeVar("_RT")
_ET = TypeVar("_ET")
_SpecificationOrFactory = Union[Specification, SpecificationFactory]


def _static_params(sample: Sample, options: Options) -> StaticParameters:
    return sample[0 : len(options.static_parameters)]  # type: ignore


def _interpolators(sample: Sample, options: Options) -> SignalInterpolators:
    start = len(options.static_parameters)
    interpolators: List[SignalInterpolator] = []

    for signal in options.signals:
        factory = signal.factory
        end = start + signal.control_points
        interpolators.append(factory.create(signal.interval.astuple(), sample[start:end]))
        start = end

    return interpolators


def _time(fn: Callable[[], _RT]) -> Tuple[float, _RT]:
    t_start = time.perf_counter()
    result = fn()
    t_stop = time.perf_counter()

    return t_stop - t_start, result


def _make_spec(sample: Sample, spec: _SpecificationOrFactory) -> Specification:
    if isinstance(spec, Specification):
        return spec
    else:
        return spec(sample)


def _result_cost(result: ModelResult[Any], spec: Specification) -> float:
    if isinstance(result, (SimulationResult, Falsification)):
        return result.eval_using(spec)
    else:
        raise TypeError(f"Unknown result type {type(result)}")


class CostFn(OptimizationFn, Generic[_ET]):
    def __init__(self, model: Model[_ET], specification: _SpecificationOrFactory, options: Options):
        self.model = model
        self.spec = specification
        self.options = options
        self._iterations: Deque[Iteration[_ET]] = deque()

    def __call__(self, sample: Sample) -> float:
        static_params = _static_params(sample, self.options)
        interpolators = _interpolators(sample, self.options)
        spec = _make_spec(sample, self.spec)

        model_params = SimulationParams(static_params, interpolators, self.options.interval)
        model_result = self.model.simulate(model_params)
        cost = _result_cost(model_result, spec)

        self._iterations.append(Iteration(cost, sample, model_result.data))

        return cost

    @property
    def iterations(self) -> List[Iteration[_ET]]:
        return list(self._iterations)


class TimedCostFn(OptimizationFn, Generic[_ET]):
    def __init__(self, model: Model[_ET], specification: _SpecificationOrFactory, options: Options):
        self.model = model
        self.spec = specification
        self.options = options
        self._iterations: Deque[TimedIteration[_ET]] = deque()

    def __call__(self, sample: Sample) -> float:
        static_params = _static_params(sample, self.options)
        interpolators = _interpolators(sample, self.options)
        spec = _make_spec(sample, self.spec)

        model_params = SimulationParams(static_params, interpolators, self.options.interval)
        model_duration, model_result = _time(lambda: self.model.simulate(model_params))
        cost_duration, cost = _time(lambda: _result_cost(model_result, spec))

        self._iterations.append(
            TimedIteration(cost, sample, model_result.data, model_duration, cost_duration)
        )

        return cost

    @property
    def iterations(self) -> List[TimedIteration[_ET]]:
        return list(self._iterations)


ScenarioResult = Union[Result[_RT, _ET], TimedResult[_RT, _ET]]


class Scenario(Generic[_ET]):
    def __init__(self, model: Model[_ET], specification: _SpecificationOrFactory, options: Options):
        self.model = model
        self.spec = specification
        self.options = options

    @property
    def _params(self) -> Generator[OptimizationParams, None, None]:
        rng = default_rng(self.options.seed)

        for _ in range(self.options.runs):
            run_seed = rng.integers(low=0, high=sys.maxsize)

            yield OptimizationParams(
                self.options.bounds,
                self.options.iterations,
                self.options.behavior,
                run_seed,
            )

    def _run(self, optimizer: Optimizer[_RT]) -> Result[_RT, _ET]:
        def run(params: OptimizationParams) -> Run[_RT, _ET]:
            func = CostFn(self.model, self.spec, self.options)
            duration, result = _time(lambda: optimizer.optimize(func, params))

            return Run(result, func.iterations, duration)

        return Result([run(params) for params in self._params], self.options)

    def _run_timed(self, optimizer: Optimizer[_RT]) -> TimedResult[_RT, _ET]:
        def timedrun(params: OptimizationParams) -> TimedRun[_RT, _ET]:
            func = TimedCostFn(self.model, self.spec, self.options)
            duration, result = _time(lambda: optimizer.optimize(func, params))

            return TimedRun(result, func.iterations, duration)

        return TimedResult([timedrun(params) for params in self._params], self.options)

    @overload
    def run(self, optimizer: Optimizer[_RT], *, timed: Literal[True]) -> TimedResult[_RT, _ET]:
        ...

    @overload
    def run(self, optimizer: Optimizer[_RT], *, timed: Literal[False] = ...) -> Result[_RT, _ET]:
        ...

    def run(self, optimizer: Optimizer[_RT], *, timed: bool = False) -> ScenarioResult[_RT, _ET]:
        if timed:
            return self._run_timed(optimizer)
        else:
            return self._run(optimizer)

from __future__ import annotations

import math
import sys
import time
from abc import ABC, abstractmethod
from collections import deque
from typing import Generic, List, Tuple, TypeVar, Union, Deque

if sys.version_info >= (3, 9):
    from collections.abc import Callable
else:
    from typing import Callable

from numpy.random import default_rng
from typing_extensions import overload, Literal

from .models import Model, ModelResult, Falsification, StaticParameters, SignalInterpolators
from .optimizers import Optimizer, Sample, OptimizationFn, OptimizationParams
from .options import Options
from .signals import SignalInterpolator
from .specification import Specification, SpecificationFactory
from .results import Iteration, Result, TimedIteration, Run, TimedRun, TimedResult

_RT = TypeVar("_RT")
_IT = TypeVar("_IT", bound=Iteration)

_SpecificationOrFactory = Union[SpecificationFactory, Specification]


class _BaseCostFn(ABC, OptimizationFn, Generic[_IT]):
    def __init__(self, model: Model, specification: _SpecificationOrFactory, options: Options):
        self.model = model
        self.spec = specification
        self.options = options
        self.iterations: Deque[_IT] = deque()

    def _result_cost(self, result: ModelResult, spec: Specification) -> float:
        if isinstance(result, Falsification):
            return -math.inf
        else:
            return spec.evaluate(result)

    def _make_spec(self, sample: Sample) -> Specification:
        if isinstance(self.spec, Specification):
            return self.spec
        else:
            return self.spec(sample)

    @abstractmethod
    def __call__(self, sample: Sample) -> float:
        raise NotImplementedError()


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


class CostFn(_BaseCostFn[Iteration]):
    def __call__(self, sample: Sample) -> float:
        static_params = _static_params(sample, self.options)
        interpolators = _interpolators(sample, self.options)
        spec = self._make_spec(sample)
        model_result = self.model.simulate(static_params, interpolators, self.options.interval)
        cost = self._result_cost(model_result, spec)

        self.iterations.append(Iteration(cost, sample))
        return cost


def _time(fn: Callable[[], _RT]) -> Tuple[float, _RT]:
    t_start = time.perf_counter()
    result = fn()
    t_stop = time.perf_counter()

    return t_stop - t_start, result


class TimedCostFn(_BaseCostFn[TimedIteration]):
    def __call__(self, sample: Sample) -> float:
        static_params = _static_params(sample, self.options)
        interpolators = _interpolators(sample, self.options)
        spec = self._make_spec(sample)

        model_duration, model_result = _time(
            lambda: self.model.simulate(static_params, interpolators, self.options.interval)
        )
        cost_duration, cost = _time(lambda: self._result_cost(model_result, spec))

        self.iterations.append(TimedIteration(cost, sample, model_duration, cost_duration))
        return cost


def _run(
    optimizer: Optimizer[_RT], fn: _BaseCostFn[_IT], params: OptimizationParams
) -> Run[_RT, _IT]:
    run_duration, result = _time(lambda: optimizer.optimize(fn, params))
    return Run(result, list(fn.iterations), run_duration)


_CostFnFactory = Callable[[], _BaseCostFn[_IT]]
_Runs = List[Run[_RT, _IT]]


def _runs(
    optimizer: Optimizer[_RT], fn_factory: _CostFnFactory[_IT], options: Options
) -> _Runs[_RT, _IT]:
    rng = default_rng(options.seed)
    run_seeds = [rng.integers(low=0, high=sys.maxsize) for _ in range(options.runs)]
    run_params = [
        OptimizationParams(options.bounds, options.iterations, options.behavior, run_seed)
        for run_seed in run_seeds
    ]
    run_fns = [fn_factory() for _ in range(options.runs)]

    return [_run(optimizer, fn, params) for fn, params in zip(run_fns, run_params)]


ScenarioResult = Union[Result[_RT, Iteration], TimedResult[_RT, TimedIteration]]


class Scenario:
    def __init__(self, model: Model, specification: _SpecificationOrFactory, options: Options):
        self.model = model
        self.spec = specification
        self.options = options

    def _run(self, optimizer: Optimizer[_RT]) -> Result[_RT, Iteration]:
        fn_factory = lambda: CostFn(self.model, self.spec, self.options)
        runs = _runs(optimizer, fn_factory, self.options)

        return Result(runs, self.options)

    def _run_timed(self, optimizer: Optimizer[_RT]) -> TimedResult[_RT, TimedIteration]:
        fn_factory = lambda: TimedCostFn(self.model, self.spec, self.options)
        runs = _runs(optimizer, fn_factory, self.options)
        timed_runs = [TimedRun(run.result, run.history, run.duration) for run in runs]

        return TimedResult(timed_runs, self.options)

    @overload
    def run(
        self, optimizer: Optimizer[_RT], *, timed: Literal[True]
    ) -> TimedResult[_RT, TimedIteration]:
        ...

    @overload
    def run(
        self, optimizer: Optimizer[_RT], *, timed: Literal[False] = ...
    ) -> Result[_RT, Iteration]:
        ...

    def run(self, optimizer: Optimizer[_RT], *, timed: bool = False) -> ScenarioResult[_RT]:
        if timed:
            return self._run_timed(optimizer)
        else:
            return self._run(optimizer)

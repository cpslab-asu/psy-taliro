from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from math import inf
from sys import maxsize
from time import perf_counter
from typing import Generic, List, Literal, Tuple, TypeVar, Union, overload, Callable

from numpy import generic
from numpy.random import default_rng
from numpy.typing import NDArray

from .models import Model, ModelResult, Falsification
from .optimizers import Optimizer, Sample, OptimizationFn, OptimizationParams
from .options import Options
from .signals import SignalInterpolator
from .specification import Specification
from .results import Iteration, Result, TimedIteration, Run, TimedRun, TimedResult

_T = TypeVar("_T", bound=generic)
_RT = TypeVar("_RT")
_IT = TypeVar("_IT", bound=Iteration)


class _BaseCostFn(ABC, OptimizationFn, Generic[_IT]):
    def __init__(self, model: Model, specification: Specification, options: Options):
        self.model = model
        self.spec = specification
        self.options = options
        self.iterations: deque[_IT] = deque()

    def _result_cost(self, result: ModelResult) -> float:
        if isinstance(result, Falsification):
            return -inf
        else:
            return self.spec.evaluate(result)

    @abstractmethod
    def __call__(self, sample: Sample) -> float:
        raise NotImplementedError()


def _static_parameters(values: NDArray[_T], options: Options) -> NDArray[_T]:
    return values[0 : len(options.static_parameters)]  # type: ignore


_Interpolators = List[SignalInterpolator]


def _signal_interpolators(values: Sample, options: Options) -> _Interpolators:
    start = len(options.static_parameters)
    interpolators: List[SignalInterpolator] = []

    for signal in options.signals:
        factory = signal.factory
        end = start + signal.control_points
        interpolators.append(factory.create(signal.interval.astuple(), values[start:end]))
        start = end

    return interpolators


class CostFn(_BaseCostFn[Iteration]):
    def __call__(self, sample: Sample) -> float:
        static_params = _static_parameters(sample, self.options)
        interpolators = _signal_interpolators(sample, self.options)
        model_result = self.model.simulate(static_params, interpolators, self.options.interval)
        cost = self._result_cost(model_result)

        self.iterations.append(Iteration(cost, sample))
        return cost


def _time(fn: Callable[[], _RT]) -> Tuple[float, _RT]:
    t_start = perf_counter()
    result = fn()
    t_stop = perf_counter()

    return t_stop - t_start, result


class TimedCostFn(_BaseCostFn[TimedIteration]):
    def __call__(self, sample: Sample) -> float:
        static_params = _static_parameters(sample, self.options)
        interpolators = _signal_interpolators(sample, self.options)

        model_duration, model_result = _time(
            lambda: self.model.simulate(static_params, interpolators, self.options.interval)
        )
        cost_duration, cost = _time(lambda: self._result_cost(model_result))

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
    run_seeds = [rng.integers(low=0, high=maxsize) for _ in range(options.runs)]
    run_params = [
        OptimizationParams(options.bounds, options.iterations, options.behavior, run_seed)
        for run_seed in run_seeds
    ]
    run_fns = [fn_factory() for _ in range(options.runs)]

    return [_run(optimizer, fn, params) for fn, params in zip(run_fns, run_params)]


ScenarioResult = Union[Result[_RT, Iteration], TimedResult[_RT, TimedIteration]]


class Scenario:
    def __init__(self, model: Model, specification: Specification, options: Options):
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

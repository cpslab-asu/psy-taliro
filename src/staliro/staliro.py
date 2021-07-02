from __future__ import annotations

import sys
from logging import getLogger, NullHandler
from math import inf
from time import perf_counter
from typing import Callable, Generic, TypeVar, List

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

from numpy import generic
from numpy.typing import NDArray
from numpy.random import default_rng

from .models import Model, Falsification
from .options import StaliroOptions
from .optimizers import Optimizer, Sample, RunOptions, OptimizerResult
from .results import StaliroResult, Run, Iteration, TimedIteration
from .specification import Specification
from .signals import SignalInterpolator

logger = getLogger("staliro")
logger.addHandler(NullHandler())

_T = TypeVar("_T", bound=generic)


def _static_parameters(values: NDArray[_T], options: StaliroOptions) -> NDArray[_T]:
    return values[0 : len(options.static_parameters)]  # type: ignore


_Interpolators = List[SignalInterpolator]


def _signal_interpolators(values: Sample, options: StaliroOptions) -> _Interpolators:
    start = len(options.static_parameters)
    interpolators: List[SignalInterpolator] = []

    for signal in options.signals:
        factory = signal.factory
        end = start + signal.control_points
        interpolators.append(factory.create(signal.interval.astuple(), values[start:end]))
        start = end

    return interpolators


_IT = TypeVar("_IT", bound=Iteration)


class CostFn(Protocol[_IT]):
    iterations: List[_IT]

    def __call__(self, sample: Sample) -> float:
        ...


_RT = TypeVar("_RT", bound=OptimizerResult)
_CostFnFactory = Callable[[Model, Specification, StaliroOptions], CostFn[_IT]]
_Runs = List[Run[_RT, _IT]]


class RunManager(Generic[_RT, _IT]):
    def __init__(self, optimizer: Optimizer[_RT], fn_factory: _CostFnFactory[_IT]):
        self.fn_factory = fn_factory
        self.optimizer = optimizer

    def execute(self, mdl: Model, spec: Specification, options: StaliroOptions) -> _Runs[_RT, _IT]:
        rng = default_rng(options.seed)
        runs: list[Run[_RT, _IT]] = []

        for _ in range(options.runs):
            cost_fn = self.fn_factory(mdl, spec, options)
            run_seed = rng.integers(low=0, high=sys.maxsize)
            run_options = RunOptions(
                options.bounds, options.iterations, options.behavior, run_seed
            )

            run_start = perf_counter()
            result = self.optimizer.optimize(cost_fn, run_options)
            run_stop = perf_counter()

            run = Run(result, cost_fn.iterations, run_stop - run_start)
            runs.append(run)

        return runs


class BasicCostFn(CostFn[Iteration]):
    def __init__(self, model: Model, specification: Specification, options: StaliroOptions):
        self.model = model
        self.spec = specification
        self.options = options
        self.iterations: list[Iteration] = []

    def __call__(self, sample: Sample) -> float:
        static_params = _static_parameters(sample, self.options)
        interpolators = _signal_interpolators(sample, self.options)
        result = self.model.simulate(static_params, interpolators, self.options.interval)

        if isinstance(result, Falsification):
            cost = -inf
        else:
            cost = self.spec.evaluate(result)

        self.iterations.append(Iteration(cost, sample))
        return cost


def staliro(
    model: Model, specification: Specification, optimizer: Optimizer[_RT], options: StaliroOptions
) -> StaliroResult[_RT, Iteration]:
    """Search for falsifying inputs to the provided system.

    Using the optimizer, search the input space defined in the options for cases which falsify the
    provided specification represented by the formula phi and the predicates.

    Args:
        model: The model of the system being tested
        specification: The requirement for the system
        options: General options to manipulate the behavior of the search
        optimizer_cls: The class of the optimizer to use to search the sample space

    Returns:
        results: A list of result objects corresponding to each run from the optimizer
    """
    manager = RunManager(optimizer, lambda m, s, o: BasicCostFn(m, s, o))
    runs = manager.execute(model, specification, options)

    return StaliroResult(runs, options.seed)


class TimedCostFn(CostFn[TimedIteration]):
    def __init__(self, model: Model, specification: Specification, options: StaliroOptions):
        self.model = model
        self.spec = specification
        self.options = options
        self.iterations: list[TimedIteration] = []

    def __call__(self, sample: Sample) -> float:
        static_params = _static_parameters(sample, self.options)
        interpolators = _signal_interpolators(sample, self.options)

        model_start_t = perf_counter()
        model_result = self.model.simulate(static_params, interpolators, self.options.interval)
        model_stop_t = perf_counter()
        model_duration = model_stop_t - model_start_t

        if isinstance(model_result, Falsification):
            cost = -inf
            cost_duration = 0.0
        else:
            cost_start_t = perf_counter()
            cost = self.spec.evaluate(model_result)
            cost_stop_t = perf_counter()
            cost_duration = cost_stop_t - cost_start_t

        self.iterations.append(TimedIteration(cost, sample, model_duration, cost_duration))
        return cost


def staliro_timed(
    model: Model, specification: Specification, optimizer: Optimizer[_RT], options: StaliroOptions
) -> StaliroResult[_RT, TimedIteration]:
    """Search for falsifying inputs to the provided system and time system components.

    Using the optimizer, search the input space defined in the options for cases which falsify the
    provided specification represented by the formula phi and the predicates. The time for each
    simulation and each cost computation is stored during execution.

    Args:
        model: The model of the system being tested
        specification: The requirement for the system
        options: General options to manipulate the behavior of the search
        optimizer_cls: The class of the optimizer to use to search the sample space

    Returns:
        results: A list of result objects corresponding to each run from the optimizer
    """
    manager = RunManager(optimizer, lambda m, s, o: TimedCostFn(m, s, o))
    runs = manager.execute(model, specification, options)

    return StaliroResult(runs, options.seed)

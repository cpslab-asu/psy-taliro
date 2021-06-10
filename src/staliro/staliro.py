from __future__ import annotations

from logging import getLogger, NullHandler
from math import inf
from random import randint
from sys import maxsize
from typing import TypeVar, List

from numpy import ndarray
from numpy.random import default_rng

from .models import Model, SimulationResult, Falsification
from .options import StaliroOptions
from .optimizers import Optimizer, ObjectiveFn, Run, RunOptions
from .results import StaliroResult
from .specification import Specification
from .signals import SignalInterpolator


def _static_parameters(values: ndarray, options: StaliroOptions) -> ndarray:
    stop = len(options.static_parameters)
    return values[0:stop]  # type: ignore


def _signal_interpolators(values: ndarray, options: StaliroOptions) -> List[SignalInterpolator]:
    start = len(options.static_parameters)
    interpolators: List[SignalInterpolator] = []

    for signal in options.signals:
        factory = signal.factory
        end = start + signal.control_points
        interpolators.append(factory.create(signal.interval.astuple(), values[start:end]))
        start = end

    return interpolators


logger = getLogger("staliro")
logger.addHandler(NullHandler())


def _make_objective_fn(spec: Specification, model: Model, options: StaliroOptions) -> ObjectiveFn:
    def objective_fn(values: ndarray) -> float:
        static_params = _static_parameters(values, options)
        interpolators = _signal_interpolators(values, options)
        result = model.simulate(static_params, interpolators, options.interval)

        if isinstance(result, SimulationResult):
            robustness = spec.evaluate(result)
        elif isinstance(result, Falsification):
            robustness = -inf
        else:
            raise ValueError(f"Unexpected return type {type(result)}")

        logger.debug(f"{values} -> {robustness}")

        return robustness

    return objective_fn


_T = TypeVar("_T", bound=Run)


def staliro(
    specification: Specification,
    model: Model,
    options: StaliroOptions,
    optimizer: Optimizer[_T],
) -> StaliroResult:
    """Search for falsifying inputs to the provided system.

    Using the optimizer, search the input space defined in the options for cases which falsify the
    provided specification represented by the formula phi and the predicates.

    Args:
        specification: The requirement for the system
        model: The model of the system being tested
        options: General options to manipulate the behavior of the search
        optimizer_cls: The class of the optimizer to use to search the sample space
        optimizer_options: Specific options to manipulate the behavior of the specific optimizer

    Returns:
        results: A list of result objects corresponding to each run from the optimizer
    """
    if not isinstance(specification, Specification):
        raise ValueError()

    if not isinstance(model, Model):
        raise ValueError()

    if not isinstance(options, StaliroOptions):
        raise ValueError()

    if not isinstance(optimizer, Optimizer):
        raise ValueError()

    objective_fn = _make_objective_fn(specification, model, options)
    seed = options.seed if options.seed is not None else randint(0, maxsize)
    rng = default_rng(seed)
    seeds = rng.integers(low=0, high=maxsize, size=options.runs)
    runs_options = [
        RunOptions(options.bounds, options.iterations, options.behavior, seed) for seed in seeds
    ]
    runs = [optimizer.optimize(objective_fn, run_options) for run_options in runs_options]

    return StaliroResult(runs, seed)

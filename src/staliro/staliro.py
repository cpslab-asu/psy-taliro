from __future__ import annotations

from logging import getLogger, NullHandler
from math import inf
from typing import Optional, TypeVar, List

from numpy import ndarray

from .models import Model, Observations, Falsification
from .options import StaliroOptions
from .optimizers import Optimizer, ObjectiveFn
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

        if isinstance(result, Observations):
            robustness = spec.evaluate(result.trajectories, result.timestamps)
        elif isinstance(result, Falsification):
            robustness = -inf
        else:
            raise ValueError(f"Unexpected return type {type(result)}")

        logger.debug(f"{values} -> {robustness}")

        return robustness

    return objective_fn


_T = TypeVar("_T", bound=StaliroResult)
_O = TypeVar("_O", contravariant=True)


def staliro(
    specification: Specification,
    model: Model,
    options: StaliroOptions,
    optimizer: Optimizer[_O, _T],
    optimizer_options: Optional[_O] = None,
) -> _T:
    """Search for falsifying inputs to the provided system.

    Using the optimizer, search the input space defined in the options for cases which falsify the
    provided specification represented by the formula phi and the predicates.

    Args:
        specification: The requirement for the system
        model: The model of the system being tested
        options: General options to manipulate the behavior of the search
        optimizer: The optimizer to use to search the sample space
        optimizer_options: Specific options to manipulate the behavior of the specific optimizer

    Returns:
        results: A list of result objects corresponding to each run from the optimizer
    """
    if not isinstance(specification, Specification):
        raise ValueError

    if not isinstance(model, Model):
        raise ValueError

    if not isinstance(options, StaliroOptions):
        raise ValueError

    if not isinstance(optimizer, Optimizer):
        raise ValueError

    objective_fn = _make_objective_fn(specification, model, options)

    if optimizer_options is None:
        return optimizer.optimize(objective_fn, options)

    return optimizer.optimize(objective_fn, options, optimizer_options)

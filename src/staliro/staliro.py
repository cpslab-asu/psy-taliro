from __future__ import annotations

from logging import getLogger, NullHandler
from typing import Optional, TypeVar, Tuple

from numpy import ndarray

from .models import Model, ModelResult
from .options import StaliroOptions
from .optimizers import Optimizer, ObjectiveFn
from .results import StaliroResult
from .specification import Specification

logger = getLogger("staliro")
logger.addHandler(NullHandler())


def _validate_result(result: ModelResult) -> Tuple[ndarray, ndarray]:
    """Ensure that the results conform to the expected dimensions."""
    trajectories, timestamps = result

    if timestamps.ndim != 1:
        raise ValueError("timestamps must be 1-dimensional")

    if trajectories.ndim != 2:
        raise ValueError("trajectories must be 2-dimensional")

    if trajectories.shape[0] != timestamps.size and trajectories.shape[1] != timestamps.size:
        raise ValueError("one dimension of trajectories must equal size of timestamps")

    if trajectories.shape[1] == timestamps.size:
        return trajectories, timestamps
    else:
        return trajectories.T, timestamps


def _make_obj_fn(spec: Specification, model: Model, options: StaliroOptions) -> ObjectiveFn:
    def obj_fn(values: ndarray) -> float:
        result = model.simulate(values, options)
        trajectories, timestamps = _validate_result(result)
        robustness = spec.evaluate(trajectories, timestamps)

        logger.debug(f"{values} -> {robustness}")
        return robustness

    return obj_fn


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

    objective_fn = _make_obj_fn(specification, model, options)

    if optimizer_options is None:
        return optimizer.optimize(objective_fn, options)

    return optimizer.optimize(objective_fn, options, optimizer_options)

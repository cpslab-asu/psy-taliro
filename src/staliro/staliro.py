from __future__ import annotations

from functools import partial
from typing import Dict, Optional, Sequence, TypeVar, Tuple

from numpy import ndarray, float32

from .models import Model, ModelResult
from .options import StaliroOptions
from .optimizers import Optimizer
from .results import StaliroResult
from .specification import Specification


def _validate_results(result: ModelResult) -> Tuple[ndarray, ndarray]:
    """Ensure that the results conform to the expected dimensions."""
    trajectories, timestamps = result

    if timestamps.ndim != 1:
        raise ValueError("timestamps must be 1-dimensional")

    if trajectories.ndim != 2:
        raise ValueError("trajectories must be 2-dimensional")
    elif trajectories.shape[0] != timestamps.size:
        raise ValueError("first dimension of trajectories must equal size of timestamps")

    return trajectories, timestamps.astype(float32)


def _compute_robustness(
    spec: Specification,
    pred_names: Sequence[str],
    model: Model,
    options: StaliroOptions,
    values: ndarray,
) -> float:
    results = model.simulate(values, options)
    trajectories, timestamps = _validate_results(results)
    traces: Dict[str, ndarray] = {pred_name: trajectories.T for pred_name in pred_names}

    return spec.evaluate(traces, timestamps)


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
        phi: The specification written as an STL formula
        preds: The predicates for the formula
        model: The model of the system being tested
        options: General options to manipulate the behavior of the search
        optimizer: The optimizer to use to search the sample space
        optimizer_options: Specific options to manipulate the behavior of the specific optimizer

    Returns:
        results: A list of result objects corresponding to each run from the optimizer
    """

    objective_fn = partial(
        _compute_robustness, specification, specification.data_keys(), model, options
    )

    if optimizer_options is None:
        return optimizer.optimize(objective_fn, options)

    return optimizer.optimize(objective_fn, options, optimizer_options)

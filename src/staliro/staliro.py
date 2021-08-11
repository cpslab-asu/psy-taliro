from __future__ import annotations

from typing import TypeVar, Union

from .models import Model
from .options import Options
from .optimizers import Optimizer
from .results import Result
from .scenarios import Scenario
from .specification import Specification, SpecificationFactory

_RT = TypeVar("_RT")
_ET = TypeVar("_ET")


def staliro(
    model: Model[_ET],
    specification: Union[Specification, SpecificationFactory],
    optimizer: Optimizer[_RT],
    options: Options,
) -> Result[_RT, _ET]:
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

    return Scenario(model, specification, options).run(optimizer)

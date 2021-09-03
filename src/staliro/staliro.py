from __future__ import annotations

from typing import TypeVar

from .core.cost import SpecificationOrFactory
from .core.model import Model
from .options import Options
from .core.optimizer import Optimizer
from .core.result import Result
from .core.scenario import Scenario

RT = TypeVar("RT")
ET = TypeVar("ET")


def staliro(
    model: Model[ET],
    specification: SpecificationOrFactory,
    optimizer: Optimizer[RT],
    options: Options,
) -> Result[RT, ET]:
    """Search for falsifying inputs to the provided system.

    Using the optimizer, search the input space defined in the options for cases which falsify the
    provided specification represented by the formula phi and the predicates.

    Args:
        model: The model of the system being tested.
        specification: The requirement for the system.
        optimizer: The optimizer to use to search the sample space.
        options: General options to manipulate the behavior of the search.

    Returns:
        An object containing the result of each optimization attempt.
    """

    return Scenario(model, specification, options).run(optimizer)

from __future__ import annotations

from logging import getLogger, NullHandler
from typing import TypeVar

from .models import Model
from .options import Options
from .optimizers import Optimizer
from .results import Result, Iteration, TimedIteration, TimedResult
from .scenarios import Scenario
from .specification import Specification

logger = getLogger("staliro")
logger.addHandler(NullHandler())

_RT = TypeVar("_RT")


def staliro(
    model: Model, specification: Specification, optimizer: Optimizer[_RT], options: Options
) -> Result[_RT, Iteration]:
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


def staliro_timed(
    model: Model, specification: Specification, optimizer: Optimizer[_RT], options: Options
) -> TimedResult[_RT, TimedIteration]:
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

    return Scenario(model, specification, options).run(optimizer, timed=True)

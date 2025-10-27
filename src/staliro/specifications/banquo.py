from typing import TypeVar

import banquo

from ..cost_func import Result
from ..models import Trace
from .specification import Specification

State = TypeVar("State")
Cost = TypeVar("Cost")


class Banquo(Specification[State, Cost, None]):
    """A system specification represented as Banquo formula.

    Args:
        formula: The system specification
    """

    def __init__(self, formula: banquo.Formula[State, Cost]):
        self.formula = formula

    def evaluate(self, trace: Trace[State]) -> Result[Cost, None]:
        bqtrace = banquo.Trace.from_timed_states(trace.times, trace.states) # Convert trace type
        rho = banquo.evaluate(self.formula, bqtrace)

        return Result(rho, None)

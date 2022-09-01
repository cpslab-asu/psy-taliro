from __future__ import annotations

from typing import Sequence, TypeVar

from numpy import float_
from numpy.typing import NDArray
from typing_extensions import Protocol, runtime_checkable

StateT = TypeVar("StateT", contravariant=True)
CostT = TypeVar("CostT", covariant=True)


@runtime_checkable
class Specification(Protocol[StateT, CostT]):
    """Class that represents a requirement to be evaluated using simulation data.

    A specification should accept the trajectories and timestamps generated by a model and return
    a value which represents the "goodness" of the model results with respect to some criteria.
    """

    @property
    def failure_cost(self) -> CostT:
        ...

    def evaluate(self, state: Sequence[StateT], timestamps: Sequence[float]) -> CostT:
        """Evaluate trajectories and timestamps with respect to some requirement.

        Args:
            trajectories: Matrix of states where each row represents a state variable.
            timestamps: Vector of time values corresponding to each column of the trajectories
                        matrix.

        Returns:
            A value indicating the "goodness" of the trajectories according to the requirement.
        """
        ...


class SpecificationError(Exception):
    pass

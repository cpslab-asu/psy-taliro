from __future__ import annotations

from numpy import float_
from numpy.typing import NDArray
from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class Specification(Protocol):
    """Class that represents a requirement to be evaluated using simulation data.

    A specification should accept the trajectories and timestamps generated by a model and return
    a value which represents the "goodness" of the model results with respect to some criteria.
    """

    def evaluate(self, states: NDArray[float_], timestamps: NDArray[float_]) -> float:
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

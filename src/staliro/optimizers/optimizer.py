from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar, Generic, Sequence, Any

from ..cost import CostFn
from ..options import Interval, Behavior

OptimizationFn = CostFn[Any]


@dataclass(frozen=True)
class OptimizationParams:
    bounds: Sequence[Interval]
    iterations: int
    behavior: Behavior
    seed: int


_T = TypeVar("_T")


class Optimizer(ABC, Generic[_T]):
    """Class that represents an optimization approach.

    An optimizer is responsible for producing samples that are provided to the optimization
    function. Calling the optimization function yields a float value which can be used to inform
    the selection of future samples. An optimizer can return any value of any type, but

    The OptimizationFn is capable of accepting one or many samples for evaluation.

    It is not recommended to store state on the optimization object because when multiple
    optimization attempts are run in parallel the optimizer instance is shared between them so any
    stateful operations may encounter race conditions.
    """

    @abstractmethod
    def optimize(self, func: OptimizationFn, params: OptimizationParams) -> _T:
        """Minimize the given function according to the provided parameters.

        Args:
            func: Function to minimize.
            params: Parameters to control the optimization behavior

        Returns:
            An optimizer-defined value.
        """

        raise NotImplementedError()

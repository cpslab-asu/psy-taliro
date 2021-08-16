from __future__ import annotations

import os
import sys
import statistics as stats
from dataclasses import dataclass
from itertools import takewhile
from typing import Optional, Union

if sys.version_info >= (3, 9):
    from collections.abc import Sequence, Iterable
else:
    from typing import Sequence, Iterable

import numpy as np
from numpy.typing import NDArray
from numpy.random import default_rng, Generator
from typing_extensions import Literal

from ..options import Interval, Behavior
from .optimizer import Optimizer, OptimizationParams, OptimizationFn


_Sample = NDArray[np.float_]
_Samples = Sequence[_Sample]


@dataclass(frozen=True)
class UniformRandomResult:
    """Data class that represents the result of a uniform random optimization.

    Attributes:
        average_cost: The average cost of all the samples selected.
    """

    average_cost: float


def _sample(bounds: Sequence[Interval], rng: Generator) -> _Sample:
    return np.array([rng.uniform(bound.lower, bound.upper) for bound in bounds])


def _minimize(samples: _Samples, func: OptimizationFn, processes: Optional[int]) -> Iterable[float]:
    if processes is None:
        return func.eval_samples(samples)
    else:
        return func.eval_samples_parallel(samples, processes)


def _falsify(samples: _Samples, func: OptimizationFn) -> Iterable[float]:
    costs = map(func.eval_sample, samples)
    return takewhile(lambda c: c >= 0, costs)


class UniformRandom(Optimizer[UniformRandomResult]):
    """Optimizer that implements the uniform random optimization technique.

    This optimizer picks samples randomly from the search space until the budget is exhausted.

    Args:
        parallelization: Value that indicates how many processes to use when evaluating each
                            sample using the cost function. Acceptable values are a number,
                            "cores", or None

    Attributes:
        processes: The number of processes to use when evaluating the samples.
    """

    def __init__(self, parallelization: Union[Literal["cores"], int, None] = None):
        if isinstance(parallelization, int):
            self.processes: Optional[int] = parallelization
        elif parallelization == "cores":
            self.processes = os.cpu_count()
        else:
            self.processes = None

    def optimize(self, func: OptimizationFn, params: OptimizationParams) -> UniformRandomResult:
        rng = default_rng(params.seed)
        samples = [_sample(params.bounds, rng) for _ in range(params.iterations)]

        if params.behavior is Behavior.MINIMIZATION:
            costs = _minimize(samples, func, self.processes)
        else:
            costs = _falsify(samples, func)

        average_cost = stats.mean(costs)

        return UniformRandomResult(average_cost)

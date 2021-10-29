from __future__ import annotations

import enum
import os
import statistics as stats
from itertools import takewhile
from typing import Iterable, Optional, Sequence, Union

import numpy as np
from attr import frozen
from numpy.random import Generator, default_rng
from numpy.typing import NDArray
from scipy import optimize
from typing_extensions import Literal

from .core.interval import Interval
from .core.optimizer import Optimizer, ObjectiveFn
from .core.sample import Sample

Samples = Sequence[Sample]
Bounds = Sequence[Interval]


class Behavior(enum.IntEnum):
    """Behavior when falsifying case for system is encountered.

    Attributes:
        FALSIFICATION: Stop searching when the first falsifying case is encountered
        MINIMIZATION: Continue searching after encountering a falsifying case until iteration
                      budget is exhausted
    """

    FALSIFICATION = enum.auto()
    MINIMIZATION = enum.auto()


@frozen(slots=True)
class UniformRandomResult:
    """Data class that represents the result of a uniform random optimization.

    Attributes:
        average_cost: The average cost of all the samples selected.
    """

    average_cost: float


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

    def __init__(
        self,
        parallelization: Union[Literal["cores"], int, None] = None,
        behavior: Behavior = Behavior.FALSIFICATION,
    ):
        if isinstance(parallelization, int):
            self.processes: Optional[int] = parallelization
        elif parallelization == "cores":
            self.processes = os.cpu_count()
        else:
            self.processes = None

        self.behavior = behavior

    def optimize(
        self, func: ObjectiveFn, bounds: Bounds, budget: int, seed: int
    ) -> UniformRandomResult:
        def sample_uniform(bounds: Bounds, rng: Generator) -> Sample:
            return Sample([rng.uniform(bound.lower, bound.upper) for bound in bounds])

        def minimize(samples: Samples, func: ObjectiveFn, nprocs: Optional[int]) -> Iterable[float]:
            if nprocs is None:
                return func.eval_samples(samples)
            else:
                return func.eval_samples_parallel(samples, nprocs)

        def falsify(samples: Samples, func: ObjectiveFn) -> Iterable[float]:
            costs = map(func.eval_sample, samples)
            return takewhile(lambda c: c >= 0, costs)

        rng = default_rng(seed)
        samples = [sample_uniform(bounds, rng) for _ in range(budget)]

        if self.behavior is Behavior.MINIMIZATION:
            costs = minimize(samples, func, self.processes)
        else:
            costs = falsify(samples, func)

        average_cost = stats.mean(costs)

        return UniformRandomResult(average_cost)


@frozen(slots=True)
class DualAnnealingResult:
    """Data class representing the result of a dual annealing optimization.

    Attributes:
        jacobian_value: The value of the cost function jacobian at the minimum cost discovered
        jacobian_evals: Number of times the jacobian of the cost function was evaluated
        hessian_value: The value of the cost function hessian as the minimum cost discovered
        hessian_evals: Number of times the hessian of the cost function was evaluated
    """

    jacobian_value: Optional[NDArray[np.float_]]
    jacobian_evals: int
    hessian_value: Optional[NDArray[np.float_]]
    hessian_evals: int


class DualAnnealing(Optimizer[DualAnnealingResult]):
    """Optimizer that implements the simulated annealing optimization technique.

    The simulated annealing implementation is provided by the SciPy library dual_annealing function
    with the no_local_search parameter set to True.
    """

    def __init__(self, behavior: Behavior = Behavior.FALSIFICATION):
        self.behavior = behavior

    def optimize(
        self, func: ObjectiveFn, bounds: Bounds, budget: int, seed: int
    ) -> DualAnnealingResult:
        def wrapper(values: NDArray[np.float_]) -> float:
            return func.eval_sample(Sample(values))

        def listener(sample: NDArray[np.float_], robustness: float, ctx: Literal[-1, 0, 1]) -> bool:
            if robustness < 0 and self.behavior is Behavior.FALSIFICATION:
                return True

            return False

        result = optimize.dual_annealing(
            wrapper,
            [bound.astuple() for bound in bounds],
            seed=seed,
            maxfun=budget,
            no_local_search=True,  # Disable local search, use only traditional generalized SA
            callback=listener,
        )

        try:
            jac: Optional[NDArray[np.float_]] = result.jac
            njev = result.njev
        except AttributeError:
            jac = None
            njev = 0

        try:
            hess: Optional[NDArray[np.float_]] = result.hess
            nhev = result.nhev
        except AttributeError:
            hess = None
            nhev = 0

        return DualAnnealingResult(jac, njev, hess, nhev)

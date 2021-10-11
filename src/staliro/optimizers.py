from __future__ import annotations

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
from .core.optimizer import Optimizer, OptimizationParams, Behavior, ObjectiveFn
from .core.sample import Sample

Samples = Sequence[Sample]


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

    def __init__(self, parallelization: Union[Literal["cores"], int, None] = None):
        if isinstance(parallelization, int):
            self.processes: Optional[int] = parallelization
        elif parallelization == "cores":
            self.processes = os.cpu_count()
        else:
            self.processes = None

    def optimize(self, func: ObjectiveFn, params: OptimizationParams) -> UniformRandomResult:
        def sample_uniform(bounds: Sequence[Interval], rng: Generator) -> Sample:
            return Sample([rng.uniform(bound.lower, bound.upper) for bound in bounds])

        def minimize(samples: Samples, func: ObjectiveFn, nprocs: Optional[int]) -> Iterable[float]:
            if nprocs is None:
                return func.eval_samples(samples)
            else:
                return func.eval_samples_parallel(samples, nprocs)

        def falsify(samples: Samples, func: ObjectiveFn) -> Iterable[float]:
            costs = map(func.eval_sample, samples)
            return takewhile(lambda c: c >= 0, costs)

        rng = default_rng(params.seed)
        samples = [sample_uniform(params.bounds, rng) for _ in range(params.iterations)]

        if params.behavior is Behavior.MINIMIZATION:
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

    jacobian_value: NDArray[np.float_]
    jacobian_evals: int
    hessian_value: NDArray[np.float_]
    hessian_evals: int


class DualAnnealing(Optimizer[DualAnnealingResult]):
    """Optimizer that implements the simulated annealing optimization technique.

    The simulated annealing implementation is provided by the SciPy library dual_annealing function
    with the no_local_search parameter set to True.
    """

    def optimize(self, func: ObjectiveFn, options: OptimizationParams) -> DualAnnealingResult:
        def wrapper(values: NDArray[np.float_]) -> float:
            return func.eval_sample(Sample(values))

        def listener(sample: NDArray[np.float_], robustness: float, ctx: Literal[-1, 0, 1]) -> bool:
            if robustness < 0 and options.behavior is Behavior.FALSIFICATION:
                return True

            return False

        bounds = [interval.bounds for interval in options.bounds]
        result: optimize.OptimizeResult = optimize.dual_annealing(
            wrapper,
            bounds,
            seed=options.seed,
            maxiter=options.iterations,
            no_local_search=True,  # Disable local search, use only traditional generalized SA
            callback=listener,
        )

        return DualAnnealingResult(result.jac, result.njev, result.hess, result.nhev)

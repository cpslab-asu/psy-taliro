from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy import optimize
from typing_extensions import Literal

from ..options import Behavior
from .optimizer import Optimizer, OptimizationParams, OptimizationFn

Sample = NDArray[np.float_]


@dataclass
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

    def optimize(self, func: OptimizationFn, options: OptimizationParams) -> DualAnnealingResult:
        def wrapper(sample: Sample) -> float:
            return func.eval_sample(sample)

        def listener(sample: Sample, robustness: float, ctx: Literal[-1, 0, 1]) -> bool:
            if robustness < 0 and options.behavior is Behavior.FALSIFICATION:
                return True

            return False

        bounds = [bound.astuple() for bound in options.bounds]
        result: optimize.OptimizeResult = optimize.dual_annealing(
            wrapper,
            bounds,
            seed=options.seed,
            maxiter=options.iterations,
            no_local_search=True,  # Disable local search, use only traditional generalized SA
            callback=listener,
        )

        return DualAnnealingResult(result.jac, result.njev, result.hess, result.nhev)

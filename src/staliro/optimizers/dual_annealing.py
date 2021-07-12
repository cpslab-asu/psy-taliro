from __future__ import annotations

from dataclasses import dataclass

from numpy import float_
from numpy.typing import NDArray
from scipy import optimize
from typing_extensions import Literal

from .optimizer import Optimizer, OptimizationFn, OptimizationParams, Sample
from ..options import Behavior


@dataclass
class DualAnnealingResult:
    jacobian_value: NDArray[float_]
    jacobian_evals: int
    hessian_value: NDArray[float_]
    hessian_evals: int


class DualAnnealing(Optimizer[DualAnnealingResult]):
    def optimize(self, func: OptimizationFn, options: OptimizationParams) -> DualAnnealingResult:
        def wrapper(sample: Sample) -> float:
            return func(sample)

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

from __future__ import annotations

from datetime import datetime
from typing import List

from numpy import ndarray
from numpy.random import default_rng
from scipy import optimize
from typing_extensions import Literal

from .optimizer import ObjectiveFn, Optimizer, Iteration, Run
from ..options import StaliroOptions, Behavior


class DualAnnealing(Optimizer[None, Run]):
    def __init__(self, options: StaliroOptions, optimizer_options: None = None):
        self.behavior = options.behavior
        self.bounds = options.bounds
        self.iterations = options.iterations

    def optimize(self, func: ObjectiveFn, seed: int) -> Run:
        history: List[Iteration] = []

        def wrapper(sample: ndarray) -> float:
            robustness = func(sample)
            history.append(Iteration(robustness, sample))

            return robustness

        def listener(sample: ndarray, robustness: float, ctx: Literal[-1, 0, 1]) -> bool:
            if robustness < 0 and self.behavior is Behavior.FALSIFICATION:
                return True

            return False

        start = datetime.now()
        bounds = [bound.astuple() for bound in self.bounds]
        optimize.dual_annealing(
            wrapper,
            bounds,
            seed=default_rng(seed),
            maxiter=self.iterations,
            no_local_search=True,  # Disable local search, use only traditional generalized SA
            callback=listener,
        )

        return Run(history, datetime.now() - start)

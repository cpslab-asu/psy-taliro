from __future__ import annotations

from datetime import datetime
from random import randint
from sys import maxsize
from typing import List

from numpy import ndarray
from numpy.random import default_rng, Generator
from scipy import optimize
from typing_extensions import Literal

from .optimizer import ObjectiveFn, Optimizer
from ..options import StaliroOptions, Behavior
from ..results import Run, Iteration, StaliroResult


def _optimize(func: ObjectiveFn, rng: Generator, options: StaliroOptions) -> Run:
    history: List[Iteration] = []

    def wrapper(sample: ndarray) -> float:
        robustness = func(sample)
        history.append(Iteration(robustness, sample))

        return robustness

    def listener(
        sample: ndarray, robustness: float, context: Literal[-1, 0, 1]
    ) -> bool:
        if robustness < 0 and options.behavior is Behavior.FALSIFICATION:
            return True

        return False

    start = datetime.now()
    bounds = [bound.astuple() for bound in options.bounds]
    optimize.dual_annealing(
        wrapper,
        bounds,
        seed=rng,
        maxiter=options.iterations,
        no_local_search=True,  # Disable local search, use only traditional generalized SA
        callback=listener,
    )

    return Run(history, datetime.now() - start)


class DualAnnealing(Optimizer[None, StaliroResult]):
    def optimize(
        self, func: ObjectiveFn, options: StaliroOptions, optimizer_options: None = None
    ) -> StaliroResult:
        seed = randint(0, maxsize) if options.seed is None else options.seed
        rng = default_rng(seed)
        runs = [_optimize(func, rng, options) for _ in range(options.runs)]

        return StaliroResult(runs, seed)

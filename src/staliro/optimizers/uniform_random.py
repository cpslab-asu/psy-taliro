from __future__ import annotations

from datetime import datetime, timedelta
from random import randint
from sys import maxsize
from typing import Iterable, Sequence, Tuple

from numpy import array, ndarray
from numpy.random import default_rng, Generator

from .optimizer import ObjectiveFn, Optimizer
from ..options import StaliroOptions, Interval, Behavior
from ..results import Run, Iteration, StaliroResult


def _sample(bounds: Sequence[Interval], rng: Generator) -> ndarray:
    return array([rng.uniform(bound.lower, bound.upper) for bound in bounds])


def _iterations(
    samples: Sequence[ndarray], func: ObjectiveFn, behavior: Behavior
) -> Iterable[Iteration]:
    for sample in samples:
        robustness = func(sample)

        yield Iteration(robustness, sample)

        if behavior is Behavior.FALSIFICATION and robustness < 0:
            break


def _optimize(
    func: ObjectiveFn, options: StaliroOptions, rng: Generator
) -> Tuple[Sequence[Iteration], timedelta]:
    start_time = datetime.now()
    samples = [_sample(options.bounds, rng) for _ in range(options.iterations)]
    iterations = list(_iterations(samples, func, options.behavior))

    return (iterations, datetime.now() - start_time)


class UniformRandom(Optimizer[None, StaliroResult]):
    def optimize(
        self, func: ObjectiveFn, options: StaliroOptions, optimizer_options: None = None
    ) -> StaliroResult:
        seed = randint(0, maxsize) if options.seed is None else options.seed
        rng = default_rng(seed)
        results = [_optimize(func, options, rng) for _ in range(options.runs)]
        runs = [Run(history, run_time) for history, run_time in results]

        return StaliroResult(runs, seed)

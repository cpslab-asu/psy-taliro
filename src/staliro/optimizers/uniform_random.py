from __future__ import annotations

from datetime import datetime
from typing import Iterable, Sequence

from numpy import array, ndarray
from numpy.random import default_rng, Generator

from .optimizer import ObjectiveFn, Optimizer, Iteration, Run
from ..options import StaliroOptions, Interval, Behavior

_Samples = Sequence[ndarray]
_Bounds = Sequence[Interval]
_Iterations = Iterable[Iteration]


def _sample(bounds: _Bounds, rng: Generator) -> ndarray:
    return array([rng.uniform(bound.lower, bound.upper) for bound in bounds])


def _iterations(samples: _Samples, func: ObjectiveFn, behavior: Behavior) -> _Iterations:
    for sample in samples:
        robustness = func(sample)

        yield Iteration(robustness, sample)

        if behavior is Behavior.FALSIFICATION and robustness < 0:
            break


class UniformRandom(Optimizer[None, Run]):
    def __init__(self, options: StaliroOptions, optimizer_options: None = None):
        self.bounds = options.bounds
        self.iterations = options.iterations
        self.behavior = options.behavior

    def optimize(self, func: ObjectiveFn, seed: int) -> Run:
        start_time = datetime.now()
        rng = default_rng(seed)
        samples = [_sample(self.bounds, rng) for _ in range(self.iterations)]
        history = list(_iterations(samples, func, self.behavior))

        return Run(history, datetime.now() - start_time)

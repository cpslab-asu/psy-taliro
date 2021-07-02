from __future__ import annotations

from typing import Sequence

from numpy import array, float_
from numpy.typing import NDArray
from numpy.random import default_rng, Generator

from .optimizer import ObjectiveFn, Optimizer, OptimizerResult, RunOptions
from ..options import Interval, Behavior


def _sample(bounds: Sequence[Interval], rng: Generator) -> NDArray[float_]:
    return array([rng.uniform(bound.lower, bound.upper) for bound in bounds])


class UniformRandom(Optimizer[OptimizerResult]):
    def optimize(self, func: ObjectiveFn, options: RunOptions) -> OptimizerResult:
        rng = default_rng(options.seed)
        samples = [_sample(options.bounds, rng) for _ in range(options.iterations)]

        for sample in samples:
            cost = func(sample)

            if options.behavior is Behavior.FALSIFICATION and cost < 0:
                break

        return OptimizerResult()

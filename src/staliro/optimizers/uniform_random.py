from __future__ import annotations

from typing import Sequence

import numpy as np
from numpy.random import default_rng, Generator
from numpy.typing import NDArray

from .optimizer import Optimizer, OptimizationFn, OptimizationParams
from ..options import Interval, Behavior


def _sample(bounds: Sequence[Interval], rng: Generator) -> NDArray[np.float_]:
    return np.array([rng.uniform(bound.lower, bound.upper) for bound in bounds])


class UniformRandom(Optimizer[None]):
    def optimize(self, func: OptimizationFn, params: OptimizationParams) -> None:
        rng = default_rng(params.seed)
        samples = [_sample(params.bounds, rng) for _ in range(params.iterations)]

        for sample in samples:
            cost = func(sample)

            if params.behavior is Behavior.FALSIFICATION and cost < 0:
                break

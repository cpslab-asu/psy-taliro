from __future__ import annotations

import sys
from itertools import takewhile
from multiprocessing import Pool
from typing import Union

if sys.version_info >= (3, 9):
    from collections.abc import Sequence
else:
    from typing import Sequence

import numpy as np
from numpy.random import default_rng, Generator
from numpy.typing import NDArray
from typing_extensions import Literal

from .optimizer import Optimizer, OptimizationFn, OptimizationParams
from ..options import Interval, Behavior


def _sample(bounds: Sequence[Interval], rng: Generator) -> NDArray[np.float_]:
    return np.array([rng.uniform(bound.lower, bound.upper) for bound in bounds])


class UniformRandom(Optimizer[None]):
    def __init__(self, parallelization: Union[Literal["cores"], int, None] = None):
        self.processes = parallelization

    def optimize(self, func: OptimizationFn, params: OptimizationParams) -> None:
        rng = default_rng(params.seed)
        samples = [_sample(params.bounds, rng) for _ in range(params.iterations)]

        if params.behavior is Behavior.MINIMIZATION:
            if self.processes is not None:
                process_count = self.processes if isinstance(self.processes, int) else None
                pool = Pool(processes=process_count)
                pool.map(func, samples)
            else:
                map(func, samples)
        else:
            takewhile(lambda s: func(s) > 0, samples)

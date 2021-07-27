from __future__ import annotations

import os
import sys
from itertools import takewhile
from typing import Union

if sys.version_info >= (3, 9):
    from collections.abc import Sequence
else:
    from typing import Sequence

import numpy as np
from pathos.multiprocessing import ProcessPool
from numpy.random import default_rng, Generator
from numpy.typing import NDArray
from typing_extensions import Literal

from .optimizer import Optimizer, OptimizationFn, OptimizationParams
from ..options import Interval, Behavior


def _sample(bounds: Sequence[Interval], rng: Generator) -> NDArray[np.float_]:
    return np.array([rng.uniform(bound.lower, bound.upper) for bound in bounds])


class UniformRandom(Optimizer[None]):
    def __init__(self, parallelization: Union[Literal["cores"], int, None] = None):
        if parallelization is not None:
            self.processes = parallelization if isinstance(parallelization, int) else os.cpu_count()
        else:
            self.processes = None

    def optimize(self, func: OptimizationFn, params: OptimizationParams) -> None:
        rng = default_rng(params.seed)
        samples = [_sample(params.bounds, rng) for _ in range(params.iterations)]

        if params.behavior is Behavior.MINIMIZATION:
            if self.processes is not None:
                pool = ProcessPool(nodes=self.processes)
                pool.map(func, samples)
            else:
                for _ in map(func, samples):
                    pass
        else:
            for _ in takewhile(lambda s: func(s) > 0, samples):
                pass

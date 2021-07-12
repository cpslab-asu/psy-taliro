from __future__ import annotations

from .optimizer import Optimizer, OptimizationFn, OptimizationParams


class Basinhopping(Optimizer[None]):
    def optimize(self, func: OptimizationFn, params: OptimizationParams) -> None:
        raise NotImplementedError()

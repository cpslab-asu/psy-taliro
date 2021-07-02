from .optimizer import Optimizer, ObjectiveFn, RunOptions, OptimizerResult


class Basinhopping(Optimizer[OptimizerResult]):
    def optimize(self, func: ObjectiveFn, options: RunOptions) -> OptimizerResult:
        raise NotImplementedError()

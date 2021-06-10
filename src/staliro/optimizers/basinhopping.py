from .optimizer import Optimizer, ObjectiveFn, Run, RunOptions


class Basinhopping(Optimizer[Run]):
    def optimize(self, func: ObjectiveFn, options: RunOptions) -> Run:
        raise NotImplementedError()

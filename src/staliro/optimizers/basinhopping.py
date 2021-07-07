from .optimizer import Optimizer, ObjectiveFn, RunOptions


class Basinhopping(Optimizer[None]):
    def optimize(self, func: ObjectiveFn, options: RunOptions) -> None:
        raise NotImplementedError()

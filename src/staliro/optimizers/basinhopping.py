from .optimizer import Optimizer, ObjectiveFn, Run
from ..options import StaliroOptions


class Basinhopping(Optimizer[None, Run]):
    def __init__(self, options: StaliroOptions, optimizer_options: None = None):
        raise NotImplementedError()

    def optimize(self, func: ObjectiveFn, seed: int) -> Run:
        raise NotImplementedError()

from .optimizer import Optimizer, ObjectiveFn
from ..options import StaliroOptions
from ..results import StaliroResult


class Basinhopping(Optimizer[None, StaliroResult]):
    def optimize(
        self, func: ObjectiveFn, options: StaliroOptions, optimizer_options: None = None
    ) -> StaliroResult:
        raise NotImplementedError()

from __future__ import annotations

import sys
from typing import Callable, TypeVar

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

from numpy import ndarray

from ..options import StaliroOptions
from ..results import StaliroResult


_T = TypeVar("_T", bound=StaliroResult, covariant=True)
_O = TypeVar("_O", contravariant=True)
ObjectiveFn = Callable[[ndarray], float]


class Optimizer(Protocol[_O, _T]):
    def optimize(
        self, func: ObjectiveFn, options: StaliroOptions, optimizer_options: _O = ...
    ) -> _T:
        ...

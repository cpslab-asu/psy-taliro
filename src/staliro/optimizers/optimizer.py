from __future__ import annotations

import sys
from typing import Callable, TypeVar

if sys.version_info >= (3, 8):
    from typing import Protocol, runtime_checkable
else:
    from typing_extensions import Protocol, runtime_checkable

from numpy import ndarray

from ..options import StaliroOptions
from ..results import StaliroResult


_T = TypeVar("_T", bound=StaliroResult, covariant=True)
_O = TypeVar("_O", contravariant=True)
ObjectiveFn = Callable[[ndarray], float]


@runtime_checkable
class Optimizer(Protocol[_O, _T]):
    def optimize(
        self, __func: ObjectiveFn, __options: StaliroOptions, __optimizer_options: _O = ...
    ) -> _T:
        ...

from __future__ import annotations

from abc import ABC
from typing import Callable, TypeVar, Generic

from numpy import ndarray

from ..options import StaliroOptions
from ..results import Run

ObjectiveFn = Callable[[ndarray], float]
_T = TypeVar("_T", bound=Run, covariant=True)
_O = TypeVar("_O", contravariant=True)


class Optimizer(ABC, Generic[_O, _T]):
    def optimize(
        self, func: ObjectiveFn, options: StaliroOptions, optimizer_options: _O = ...
    ) -> _T:
        raise NotImplementedError()

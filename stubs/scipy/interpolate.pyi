from collections.abc import Sequence
from typing import Literal, overload

from numpy import float_, int_
from numpy.typing import ArrayLike, NDArray
from typing_extensions import TypeAlias

_Extrapolate: TypeAlias = bool | Literal["periodic"] | None
_IntegralArray: TypeAlias = NDArray[float_ | int_]

_Vector: TypeAlias = NDArray[float_] | NDArray[int_] | Sequence[float]

class PchipInterpolator:
    def __init__(
        self, x: _Vector, y: _Vector, axis: int = ..., extrapolate: bool | None = ...
    ) -> None: ...
    @overload
    def __call__(self, x: float, nu: int = ..., extrapolate: _Extrapolate = ...) -> float: ...
    @overload
    def __call__(
        self, x: _Vector, nu: int = ..., extrapolate: _Extrapolate = ...
    ) -> NDArray[float_]: ...

_Kind: TypeAlias = Literal[
    "linear", "nearest", "nearest-up", "zero", "slinear", "quadratic", "cubic", "previous", "next"
]

class interp1d:
    def __init__(
        self,
        x: ArrayLike,
        y: ArrayLike,
        kind: _Kind = ...,
        axis: int = ...,
        copy: bool = ...,
        bounds_error: bool | None = ...,
        fill_value: ArrayLike | Literal["extrapolate"] = ...,
        assume_sorted: bool = ...,
    ) -> None: ...
    @overload
    def __call__(self, x: float) -> float: ...
    @overload
    def __call__(self, x: Sequence[float] | _IntegralArray) -> NDArray[float_]: ...

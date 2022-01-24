from typing import Literal, Optional, Sequence, Union, overload

from numpy import float_, int_
from numpy.typing import ArrayLike, NDArray

_Extrapolate = Union[bool, Literal["periodic"], None]
_IntegralArray = NDArray[Union[float_, int_]]

_Vector = Union[NDArray[float_], NDArray[int_], Sequence[float]]

class PchipInterpolator:
    def __init__(
        self,
        x: _Vector,
        y: _Vector,
        axis: int = ...,
        extrapolate: Optional[bool] = ...,
    ) -> None: ...
    @overload
    def __call__(self, x: float, nu: int = ..., extrapolate: _Extrapolate = ...) -> float: ...
    @overload
    def __call__(
        self,
        x: _Vector,
        nu: int = ...,
        extrapolate: _Extrapolate = ...,
    ) -> NDArray[float_]: ...

_Kind = Literal[
    "linear",
    "nearest",
    "nearest-up",
    "zero",
    "slinear",
    "quadratic",
    "cubic",
    "previous",
    "next",
]

class interp1d:
    def __init__(
        self,
        x: ArrayLike,
        y: ArrayLike,
        kind: _Kind = ...,
        axis: int = ...,
        copy: bool = ...,
        bounds_error: Optional[bool] = ...,
        fill_value: Union[ArrayLike, Literal["extrapolate"]] = ...,
        assume_sorted: bool = ...,
    ) -> None: ...
    @overload
    def __call__(self, x: float) -> float: ...
    @overload
    def __call__(self, x: Union[Sequence[float], _IntegralArray]) -> NDArray[float_]: ...

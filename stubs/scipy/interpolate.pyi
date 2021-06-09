from typing import Optional, Union, Literal, overload, Sequence

from numpy import ndarray
from numpy.typing import ArrayLike

_Extrapolate = Union[bool, Literal["periodic"], None]

class PchipInterpolator:
    def __init__(
        self, x: ndarray, y: ndarray, axis: int = ..., extrapolate: Optional[bool] = ...
    ) -> None: ...
    @overload
    def __call__(self, x: float, nu: int = ..., extrapolate: _Extrapolate = ...) -> float: ...
    @overload
    def __call__(
        self,
        x: Union[ndarray, Sequence[float]],
        nu: int = ...,
        extrapolate: _Extrapolate = ...,
    ) -> ndarray: ...

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
    def __call__(self, x: Union[Sequence[float], ndarray]) -> ndarray: ...

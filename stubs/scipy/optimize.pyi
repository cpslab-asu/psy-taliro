from collections.abc import Callable, Sequence
from typing import Any, Literal

from numpy import float_
from numpy.typing import NDArray

class OptimizeResult:
    x: NDArray[float_]
    success: bool
    status: int
    message: str
    fun: NDArray[float_]
    jac: NDArray[float_]
    hess: NDArray[float_]
    hess_inv: object
    nfev: int
    njev: int
    nhev: int
    nit: int
    maxcv: float

def dual_annealing(
    func: Callable[[NDArray[float_]], float],
    bounds: Sequence[tuple[float, float]],
    args: tuple[Any, ...] = ...,
    maxiter: int = ...,
    local_search_options: dict[str, Any] = ...,
    initial_temp: float = ...,
    restart_temp_ratio: float = ...,
    visit: float = ...,
    accept: float = ...,
    maxfun: int = ...,
    seed: int | None = ...,
    no_local_search: bool = ...,
    callback: Callable[[NDArray[float_], float, Literal[-1, 0, 1]], bool] | None = ...,
    x0: NDArray[float_] | None = ...,
) -> OptimizeResult: ...

from typing import Any, Callable, Dict, Literal, Optional, Sequence, Tuple

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
    bounds: Sequence[Tuple[float, float]],
    args: Tuple[Any, ...] = ...,
    maxiter: int = ...,
    local_search_options: Dict[str, Any] = ...,
    initial_temp: float = ...,
    restart_temp_ratio: float = ...,
    visit: float = ...,
    accept: float = ...,
    maxfun: int = ...,
    seed: Optional[int] = ...,
    no_local_search: bool = ...,
    callback: Optional[Callable[[NDArray[float_], float, Literal[-1, 0, 1]], bool]] = ...,
    x0: Optional[NDArray[float_]] = ...,
) -> OptimizeResult: ...

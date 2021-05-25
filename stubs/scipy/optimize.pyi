from typing import Callable, Sequence, Tuple, Dict, Optional, Literal, Any

from numpy import ndarray

class OptimizeResult: ...

def dual_annealing(
    func: Callable[[ndarray], float],
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
    callback: Optional[Callable[[ndarray, float, Literal[-1, 0, 1]], bool]] = ...,
    x0: Optional[ndarray] = ...,
) -> OptimizeResult: ...

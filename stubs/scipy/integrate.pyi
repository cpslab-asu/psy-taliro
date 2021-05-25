from typing import Callable, Tuple, Union, Literal, Any, Optional, List

from numpy import ndarray
from numpy.typing import ArrayLike

_ObjectiveFun = Callable[[float, ndarray], ArrayLike]
_Method = Union[
    Literal["RK45"],
    Literal["RK23"],
    Literal["DOP853"],
    Literal["Radau"],
    Literal["BDF"],
    Literal["LSODA"],
]
_EventFn = Callable[[float, ndarray], float]
_Events = Union[_EventFn, List[_EventFn]]
_Jacobian = Union[ArrayLike, Callable[[float, ndarray], ArrayLike]]

class DenseOutput:
    t_min: float
    t_max: float
    def __init__(self, t_old: float, t: float) -> None: ...
    def __call__(self, t: ArrayLike) -> ndarray: ...

class OdeSolver:
    def __init__(
        self,
        fun: _ObjectiveFun,
        t0: ArrayLike,
        t_bound: float,
        vectorized: bool,
        support_complex: bool = ...,
    ) -> None: ...
    def dense_output(self) -> DenseOutput: ...
    def step(self) -> Optional[str]: ...

class OdeSolution:
    t_min: float
    t_max: float
    def __init__(self, ts: ArrayLike, interpolants: List[DenseOutput]) -> None: ...
    def __call__(self, t: ArrayLike) -> ndarray: ...

class _IvpSolution:
    t: ndarray
    y: ndarray
    sol: Optional[OdeSolution]
    t_events: Optional[List[ndarray]]
    y_events: Optional[List[ndarray]]
    nfev: int
    njev: int
    nlu: int
    status: Union[Literal[-1], Literal[0], Literal[1]]
    message: str
    success: bool

def solve_ivp(
    fun: _ObjectiveFun,
    t_span: Tuple[float, float],
    y0: ArrayLike,
    method: Union[OdeSolver, _Method] = ...,
    t_eval: Optional[ArrayLike] = ...,
    dense_output: bool = ...,
    events: Optional[_Events] = ...,
    vectorized: bool = ...,
    args: Optional[Tuple[Any, ...]] = ...,
    first_step: Optional[float] = ...,
    max_step: float = ...,
    rtol: ArrayLike = ...,
    atol: ArrayLike = ...,
    jac: Optional[_Jacobian] = ...,
    jac_sparsity: Optional[ArrayLike] = ...,
    lband: Optional[int] = ...,
    uband: Optional[int] = ...,
    min_step: float = ...,
) -> _IvpSolution: ...

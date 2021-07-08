from typing import Callable, Tuple, Union, Literal, Any, Optional, List

from numpy import float_
from numpy.typing import ArrayLike, NDArray

_ObjectiveFun = Callable[[float, NDArray[float_]], ArrayLike]
_Method = Union[
    Literal["RK45"],
    Literal["RK23"],
    Literal["DOP853"],
    Literal["Radau"],
    Literal["BDF"],
    Literal["LSODA"],
]
_EventFn = Callable[[float, NDArray[float_]], float]
_Events = Union[_EventFn, List[_EventFn]]
_Jacobian = Union[ArrayLike, Callable[[float, NDArray[float_]], ArrayLike]]

class DenseOutput:
    t_min: float
    t_max: float
    def __init__(self, t_old: float, t: float) -> None: ...
    def __call__(self, t: ArrayLike) -> NDArray[float_]: ...

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
    def __call__(self, t: ArrayLike) -> NDArray[float_]: ...

_EventList = List[NDArray[float_]]

class _IvpSolution:
    t: NDArray[float_]
    y: NDArray[float_]
    sol: Optional[OdeSolution]
    t_events: Optional[_EventList]
    y_events: Optional[_EventList]
    nfev: int
    njev: int
    nlu: int
    status: Literal[-1, 0, 1]
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

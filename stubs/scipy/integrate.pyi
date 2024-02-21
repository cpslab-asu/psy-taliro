from collections.abc import Callable
from typing import Any, Literal

from numpy import float_
from numpy.typing import ArrayLike, NDArray
from typing_extensions import TypeAlias

_ObjectiveFun: TypeAlias = Callable[[float, NDArray[float_]], ArrayLike]
_Method: TypeAlias = Literal["RK45", "RK23", "DOP853", "Radau", "BDF", "LSODA"]

_EventFn: TypeAlias = Callable[[float, NDArray[float_]], float]
_Events: TypeAlias = _EventFn | list[_EventFn]
_Jacobian: TypeAlias = ArrayLike | Callable[[float, NDArray[float_]], ArrayLike]

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
    def step(self) -> str | None: ...

class OdeSolution:
    t_min: float
    t_max: float
    def __init__(self, ts: ArrayLike, interpolants: list[DenseOutput]) -> None: ...
    def __call__(self, t: ArrayLike) -> NDArray[float_]: ...

_EventList: TypeAlias = list[NDArray[float_]]

class _IvpSolution:
    t: NDArray[float_]
    y: NDArray[float_]
    sol: OdeSolution | None
    t_events: _EventList | None
    y_events: _EventList | None
    nfev: int
    njev: int
    nlu: int
    status: Literal[-1, 0, 1]
    message: str
    success: bool

def solve_ivp(
    fun: _ObjectiveFun,
    t_span: tuple[float, float],
    y0: ArrayLike,
    method: OdeSolver | _Method = ...,
    t_eval: ArrayLike | None = ...,
    dense_output: bool = ...,
    events: _Events | None = ...,
    vectorized: bool = ...,
    args: tuple[Any, ...] | None = ...,
    first_step: float | None = ...,
    max_step: float = ...,
    rtol: ArrayLike = ...,
    atol: ArrayLike = ...,
    jac: _Jacobian | None = ...,
    jac_sparsity: ArrayLike | None = ...,
    lband: int | None = ...,
    uband: int | None = ...,
    min_step: float = ...,
) -> _IvpSolution: ...

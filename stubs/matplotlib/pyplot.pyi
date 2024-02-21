from typing import Any

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from numpy import float_, int_
from numpy.typing import NDArray

def figure(num: int) -> None: ...
def subplot(total: int, x: int, y: int) -> None: ...
def plot(x_axis: NDArray[float_ | int_], y_axis: NDArray[float_ | int_]) -> None: ...
def show() -> None: ...
def subplots(
    nrows: int = ...,
    ncols: int = ...,
    *,
    sharex: bool = ...,
    sharey: bool = ...,
    squeeze: bool = ...,
    subplot_kw: dict[Any, Any] | None = ...,
    gridspec_kw: dict[Any, Any] | None = ...,
    **fig_kw: Any,
) -> tuple[Figure, Axes]: ...

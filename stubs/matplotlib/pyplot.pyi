from typing import Any, Dict, Optional, Tuple, Union

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from numpy import float_, int_
from numpy.typing import NDArray

def figure(num: int) -> None: ...
def subplot(total: int, x: int, y: int) -> None: ...
def plot(x_axis: NDArray[Union[float_, int_]], y_axis: NDArray[Union[float_, int_]]) -> None: ...
def show() -> None: ...
def subplots(
    nrows: int = ...,
    ncols: int = ...,
    *,
    sharex: bool = ...,
    sharey: bool = ...,
    squeeze: bool = ...,
    subplot_kw: Optional[Dict[Any, Any]] = ...,
    gridspec_kw: Optional[Dict[Any, Any]] = ...,
    **fig_kw: Any,
) -> Tuple[Figure, Axes]: ...

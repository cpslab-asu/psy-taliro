from typing import Literal

from pandas import DataFrame

def assert_frame_equal(
    left: DataFrame,
    right: DataFrame,
    check_dtype: bool = ...,
    check_index_type: Literal["equiv"] | bool = ...,
    check_frame_type: bool = ...,
    check_less_precise: int | bool = ...,
    check_names: bool = ...,
    by_blocks: bool = ...,
    check_exact: bool = ...,
    check_datetimelike_compat: bool = ...,
    check_categorical: bool = ...,
    check_like: bool = ...,
    check_freq: bool = ...,
    check_flags: bool = ...,
    rtol: float = ...,
    atol: float = ...,
    obj: str = ...,
) -> None: ...

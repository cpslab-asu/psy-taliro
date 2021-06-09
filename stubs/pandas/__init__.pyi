from __future__ import annotations

from typing import (
    Optional,
    Union,
    List,
    Literal,
    Callable,
    Dict,
    Any,
    Iterable,
    Iterator,
    Tuple,
    overload,
)

from numpy import ndarray
from numpy.typing import ArrayLike, DTypeLike

class Index: ...

class Series:
    def __init__(
        self,
        data: Union[ArrayLike, Iterable[Any], Dict[str, Any]],
        index: Union[ArrayLike, Index] = ...,
        dtype: Union[str, DTypeLike, None] = ...,
        name: Optional[str] = ...,
        copy: bool = ...,
    ) -> None: ...
    @overload
    def __getitem__(self, index: slice) -> Series: ...
    @overload
    def __getitem__(self, index: int) -> Any: ...
    @overload
    def __getitem__(self, index: str) -> Any: ...
    def __iter__(self) -> Iterator[Any]: ...
    def __len__(self) -> int: ...
    def to_numpy(
        self,
        dtype: Optional[DTypeLike] = ...,
        copy: bool = ...,
        na_value: Any = ...,
        **kwargs: Any
    ) -> ndarray: ...

_Axis = Union[Literal[0], Literal[1], Literal["index"], Literal["columns"]]

class _Loc:
    @overload
    def __getitem__(self, index: Callable[[Series], bool]) -> DataFrame: ...
    @overload
    def __getitem__(self, index: int) -> Series: ...

class _Index:
    def __getitem__(self, index: int) -> Any: ...

class DataFrame:
    def __init__(
        self,
        data: Union[ndarray, Iterable[Any], Dict[str, Any], DataFrame],
        index: Union[Index, ArrayLike],
        columns: Union[Index, ArrayLike],
        dtype: Optional[DTypeLike] = ...,
        copy: bool = ...,
    ) -> None: ...
    @overload
    def __getitem__(self, index: str) -> Series: ...
    @overload
    def __getitem__(self, index: List[str]) -> DataFrame: ...
    @overload
    def __getitem__(self, index: _Index) -> DataFrame: ...
    def apply(
        self,
        func: Callable[..., Any],
        axis: _Axis = ...,
        raw: bool = ...,
        result_type: Union[
            Literal["expand"], Literal["reduce"], Literal["broadcast"], None
        ] = ...,
        args: Tuple[Any] = ...,
        **kwds: Any
    ) -> DataFrame: ...
    def set_axis(
        self,
        labels: Union[List[str], List[int], Index],
        axis: _Axis = ...,
        inplace: bool = ...,
    ) -> DataFrame: ...
    def to_numpy(
        self,
        dtype: Optional[DTypeLike] = ...,
        copy: bool = ...,
        na_value: Any = ...,
        **kwargs: Any
    ) -> ndarray: ...
    @property
    def loc(self) -> _Loc: ...
    @property
    def iloc(self) -> _Loc: ...
    @property
    def columns(self) -> _Index: ...

_UsecolsPredicate = Callable[[str], bool]
_DtypeDict = Dict[str, DTypeLike]
_SkiprowsPredicate = Callable[[int], bool]
_Converters = Dict[Union[int, str], Callable[..., Any]]
_AnyDict = Dict[Union[str, int], Any]
_ParseDateDict = Dict[str, List[int]]
_IntMatrix = List[List[int]]
_StrMatrix = List[List[int]]

def read_csv(
    filepath_or_buffer: str,
    sep: str = ...,
    delimiter: Optional[str] = ...,
    header: Union[int, List[int], Literal["infer"]] = ...,
    names: Optional[List[str]] = ...,
    index_col: Union[int, str, List[int], List[str], Literal[False], None] = ...,
    usecols: Union[List[int], List[str], _UsecolsPredicate] = ...,
    squeeze: bool = ...,
    prefix: Optional[str] = ...,
    mangle_dupe_cols: bool = ...,
    dtype: Union[DTypeLike, _DtypeDict, None] = ...,
    engine: Union[Literal["c"], Literal["python"]] = ...,
    converters: Optional[_Converters] = ...,
    true_values: Optional[List[Any]] = ...,
    false_values: Optional[List[Any]] = ...,
    skipinitialspace: bool = ...,
    skiprows: Union[List[int], List[str], int, _SkiprowsPredicate, None] = ...,
    skipfooter: int = ...,
    nrows: Optional[int] = ...,
    na_values: Union[float, str, List[float], _AnyDict, None] = ...,
    keep_default_na: bool = ...,
    na_filter: bool = ...,
    verbose: bool = ...,
    skip_blank_lines: bool = ...,
    parse_dates: Union[
        bool,
        List[int],
        List[str],
        _IntMatrix,
        _StrMatrix,
        _ParseDateDict,
    ] = ...,
    infer_datetime_format: bool = ...,
    keep_date_col: bool = ...,
    date_parser: Any = ...,
) -> DataFrame: ...

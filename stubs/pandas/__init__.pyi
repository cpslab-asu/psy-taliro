from collections.abc import Callable, Iterable, Iterator
from typing import Any, Literal, overload

from numpy.typing import ArrayLike, DTypeLike, NDArray
from typing_extensions import TypeAlias

class Index: ...

class Series:
    def __init__(
        self,
        data: ArrayLike | Iterable[Any] | dict[str, Any],
        index: ArrayLike | Index = ...,
        dtype: str | DTypeLike | None = ...,
        name: str | None = ...,
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
        self, dtype: DTypeLike | None = ..., copy: bool = ..., na_value: Any = ..., **kwargs: Any
    ) -> NDArray[Any]: ...

_Axis: TypeAlias = Literal[0, 1, "index", "column"]

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
        data: NDArray[Any] | Iterable[Any] | dict[str, Any] | DataFrame,
        index: Index | ArrayLike,
        columns: Index | ArrayLike,
        dtype: DTypeLike | None = ...,
        copy: bool = ...,
    ) -> None: ...
    @overload
    def __getitem__(self, index: str) -> Series: ...
    @overload
    def __getitem__(self, index: list[str]) -> DataFrame: ...
    @overload
    def __getitem__(self, index: _Index) -> DataFrame | Series: ...
    def apply(
        self,
        func: Callable[..., Any],
        axis: _Axis = ...,
        raw: bool = ...,
        result_type: Literal["expand", "reduce", "broadcast"] | None = ...,
        args: tuple[Any, ...] = ...,
        **kwds: Any,
    ) -> DataFrame: ...
    def set_axis(
        self, labels: list[str] | list[int] | Index, axis: _Axis = ..., inplace: bool = ...
    ) -> DataFrame: ...
    def to_numpy(
        self, dtype: DTypeLike | None = ..., copy: bool = ..., na_value: Any = ..., **kwargs: Any
    ) -> NDArray[Any]: ...
    @property
    def loc(self) -> _Loc: ...
    @property
    def iloc(self) -> _Loc: ...
    @property
    def columns(self) -> _Index: ...

_UsecolsPredicate: TypeAlias = Callable[[str], bool]
_DtypeDict: TypeAlias = dict[str, DTypeLike]
_SkiprowsPredicate: TypeAlias = Callable[[int], bool]
_Converters: TypeAlias = dict[int | str, Callable[..., Any]]
_AnyDict: TypeAlias = dict[str | int, Any]
_ParseDateDict: TypeAlias = dict[str, list[int]]
_IntMatrix: TypeAlias = list[list[int]]
_StrMatrix: TypeAlias = list[list[int]]

def read_csv(
    filepath_or_buffer: str,
    sep: str = ...,
    delimiter: str | None = ...,
    header: int | list[int] | Literal["infer"] = ...,
    names: list[str] | None = ...,
    index_col: int | str | list[int] | list[str] | Literal[False] | None = ...,
    usecols: list[int] | list[str] | _UsecolsPredicate = ...,
    squeeze: bool = ...,
    prefix: str | None = ...,
    mangle_dupe_cols: bool = ...,
    dtype: DTypeLike | _DtypeDict | None = ...,
    engine: Literal["c", "python"] = ...,
    converters: _Converters | None = ...,
    true_values: list[Any] | None = ...,
    false_values: list[Any] | None = ...,
    skipinitialspace: bool = ...,
    skiprows: list[int] | list[str] | int | _SkiprowsPredicate | None = ...,
    skipfooter: int = ...,
    nrows: int | None = ...,
    na_values: float | str | list[float] | _AnyDict | None = ...,
    keep_default_na: bool = ...,
    na_filter: bool = ...,
    verbose: bool = ...,
    skip_blank_lines: bool = ...,
    parse_dates: bool | list[int] | list[str] | _IntMatrix | _StrMatrix | _ParseDateDict = ...,
    infer_datetime_format: bool = ...,
    keep_date_col: bool = ...,
    date_parser: Any = ...,
) -> DataFrame: ...

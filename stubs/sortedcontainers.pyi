from collections.abc import Callable, Iterable, Iterator, Mapping
from typing import Generic, Protocol, TypeVar, overload

class _SupportsLT(Protocol):
    def __lt__(self, other: object) -> bool: ...

_Key = TypeVar("_Key")
_Val = TypeVar("_Val")
_Cmp = TypeVar("_Cmp", bound=_SupportsLT)

class SortedDict(Generic[_Key, _Val]):
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(
        self,
        pairs: Iterable[tuple[_Key, _Val]],
        /,
        *,
        key: Callable[[_Key], _Cmp] = ...,
    ): ...
    @overload
    def __init__(
        self,
        mapping: Mapping[_Key, _Val],
        /,
        *,
        key: Callable[[_Key], _Cmp] = ...,
    ): ...
    def __len__(self) -> int: ...
    def __getitem__(self, key: _Key) -> _Val: ...
    def __iter__(self) -> Iterator[_Key]: ...
    def keys(self) -> Iterable[_Key]: ...
    def values(self) -> Iterable[_Val]: ...
    def items(self) -> Iterable[tuple[_Key, _Val]]: ...


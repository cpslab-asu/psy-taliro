from __future__ import annotations

import sys
from typing import List, Union, overload

if sys.version_info >= (3, 9):
    from collections.abc import Iterator, Sized, Iterable
else:
    from typing import Iterator, Sized, Iterable

from attr import frozen, field
from attr.validators import deep_iterable, instance_of


@frozen()
class Sample(Sized, Iterable[float]):
    values: List[float] = field(converter=list, validator=deep_iterable(instance_of(float)))

    def __len__(self) -> int:
        return len(self.values)

    def __iter__(self) -> Iterator[float]:
        return iter(self.values)

    @overload
    def __getitem__(self, index: int) -> float:
        ...

    @overload
    def __getitem__(self, index: slice) -> List[float]:
        ...

    def __getitem__(self, index: Union[int, slice]) -> Union[float, List[float]]:
        if isinstance(index, (int, slice)):
            return self.values[index]
        else:
            raise TypeError()

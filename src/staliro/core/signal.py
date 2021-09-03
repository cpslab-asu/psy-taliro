from __future__ import annotations

from typing import List, Sequence

from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class Signal(Protocol):
    def at_time(self, time: float) -> float:
        ...

    def at_times(self, times: Sequence[float]) -> List[float]:
        ...

from __future__ import annotations

from typing import List, Sequence

from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class Signal(Protocol):
    """Representation of a time-varying input to a system."""

    def at_time(self, time: float) -> float:
        """Get the value of the signal at the specified time."""
        ...

    def at_times(self, times: Sequence[float]) -> List[float]:
        """Get the value of the signal at each specified time."""
        ...


@runtime_checkable
class SignalFactory(Protocol):
    """Construct a Signal using the provided times and signal values."""

    def __call__(self, __times: Sequence[float], __values: Sequence[float]) -> Signal:
        ...

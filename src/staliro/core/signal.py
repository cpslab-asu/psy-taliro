from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Protocol


class Signal(ABC):
    """Representation of a time-varying input to a system."""

    @abstractmethod
    def at_time(self, time: float) -> float:
        """Get the value of the signal at the specified time."""
        ...

    def at_times(self, times: Sequence[float]) -> list[float]:
        """Get the value of the signal at each specified time."""

        return [self.at_time(time) for time in times]


class SignalFactory(Protocol):
    """Construct a Signal using the provided times and signal values."""

    def __call__(self, __times: Sequence[float], __values: Sequence[float]) -> Signal:
        ...

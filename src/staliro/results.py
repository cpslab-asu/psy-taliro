from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Sequence

from .optimizers import Run

EMPTY_TIMEDELTA = timedelta(0)


@dataclass
class StaliroResult:
    runs: Sequence[Run]
    seed: int

    @property
    def best_run(self) -> Run:
        return min(self.runs, key=lambda r: r.best_iter.robustness)

    @property
    def run_time(self) -> timedelta:
        return sum((run.run_time for run in self.runs), EMPTY_TIMEDELTA)

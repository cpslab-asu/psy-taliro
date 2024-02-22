from __future__ import annotations

from attrs import frozen

from .options import Interval


@frozen()
class TestOptions:
    seed: int
    budget: int
    input_bounds: list[Interval]
    time_bounds: Interval

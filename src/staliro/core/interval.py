from __future__ import annotations

from typing import Iterable, Iterator, Tuple, Union

from attr import Attribute, field, frozen

BoundT = Union[int, float]


class IntervalError(Exception):
    pass


def _bound_converter(bound: BoundT) -> float:
    if isinstance(bound, int):
        return float(bound)

    if isinstance(bound, float):
        return bound

    raise IntervalError(f"Expected [float, int] type for bound, recieved: {type(bound)}")


def _upper_validator(inst: Interval, _: Attribute[float], upper: float) -> None:
    if upper == inst.lower:
        raise IntervalError("interval cannot have zero length")

    if upper < inst.lower:
        raise IntervalError("interval upper bound must be greater than lower bound")


@frozen(slots=True)
class Interval(Iterable[float]):
    """Representation of an interval of values.

    Args:
        lower: The lower bound of the interval
        upper: The upper bound of the interval

    Attributes:
        bounds: The upper and lower values of the interval
        length: The length of the interval
    """

    lower: float = field(converter=_bound_converter)
    upper: float = field(converter=_bound_converter, validator=_upper_validator)

    def __iter__(self) -> Iterator[float]:
        return iter(self.astuple())

    @property
    def length(self) -> float:
        """The length of the interval."""

        return self.upper - self.lower

    def astuple(self) -> Tuple[float, float]:
        return (self.lower, self.upper)

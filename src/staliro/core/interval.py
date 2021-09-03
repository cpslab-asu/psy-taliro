from __future__ import annotations

from typing import Any, Iterable, Iterator, Tuple, Union

from attr import Attribute, field, frozen


def _int_to_float(value: Union[int, float]) -> float:
    return float(value) if type(value) is int else value


def _lower_validator(obj: Any, attr: Attribute[Any], lower: Any) -> None:
    if type(lower) is not float:
        raise TypeError(f"unknown type {type(lower)} given as lower bound")


def _upper_validator(obj: Interval, attr: Attribute[Any], upper: Any) -> None:
    if type(upper) is not float:
        raise TypeError(f"unknown type {type(upper)} given as upper bound")

    if upper == obj.lower:
        raise ValueError("interval cannot have zero length")

    if upper < obj.lower:
        raise ValueError("interval upper bound must be greater than lower bound")


@frozen()
class Interval(Iterable[float]):
    """Representation of an interval of values.

    Args:
        lower: The lower bound of the interval
        upper: The upper bound of the interval

    Attributes:
        bounds: The upper and lower values of the interval
        length: The length of the interval
    """

    lower: float = field(converter=_int_to_float, validator=_lower_validator)
    upper: float = field(converter=_int_to_float, validator=_upper_validator)

    def __iter__(self) -> Iterator[float]:
        return iter(self.bounds)

    @property
    def bounds(self) -> Tuple[float, float]:
        return (self.lower, self.upper)

    @property
    def length(self) -> float:
        """The length of the interval."""

        return self.upper - self.lower

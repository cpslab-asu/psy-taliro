from statistics import mean
from typing import (
    Dict,
    Iterable,
    Protocol,
    Literal,
    NamedTuple,
    Sequence,
    Union,
    runtime_checkable,
)

from numpy import ndarray, hstack

from .parser import parse


@runtime_checkable
class Specification(Protocol):
    def evaluate(self, trajectories: ndarray, timestamps: ndarray) -> float:
        ...


class Predicate(NamedTuple):
    column: int
    dtype: Literal["float", "int"] = "float"


class TLTK(Specification):
    """TLTk specification backend.

    Attributes:
        phi: The specification requirement
        predicates: A set of Predicate(s) used in the requirement
    """
    def __init__(self, phi: str, predicates: Dict[str, Predicate]):
        if not all(isinstance(element, Predicate) for element in predicates):
            raise ValueError("predicates must be dictionary of specification.Predicate objects")

        parsed = parse(phi, list(predicates.keys()))

        if parsed is None:
            raise RuntimeError("Could not parse requirement")

        self.tltk_obj = parsed
        self.predicates = predicates

    def evaluate(self, trajectories: ndarray, timestamps: ndarray) -> float:
        pred_map = self.predicates.items()
        traces = {name: trajectories[pred.column].astype(pred.dtype) for name, pred in pred_map}

        self.tltk_obj.reset()
        self.tltk_obj.eval_interval(traces, timestamps)

        return self.tltk_obj.robustness


def _step_widths(times: Union[Sequence[float], ndarray]) -> Iterable[float]:
    """Compute the distance between adjacent elements."""

    for i in range(len(times) - 2):
        yield abs(times[i] - times[i + 1])


class RTAMTDiscrete(Specification):
    def __init__(self, phi: str, predicates: Dict[str, Predicate]):
        try:
            from rtamt import STLDiscreteTimeSpecification
            from rtamt.enumerations.options import Semantics
        except ModuleNotFoundError:
            raise RuntimeError("RTAMT must be installed to use associated backends")

        if "time" in predicates:
            raise ValueError("'time' cannot be used as a predicate name for RTAMT")

        self.predicates = predicates
        self.rtamt_obj = STLDiscreteTimeSpecification(Semantics.STANDARD)
        self.rtamt_obj.spec = phi
        self.rtamt_obj.parse()
        self.rtamt_obj.pastify()

        for name, options in predicates.items():
            self.rtamt_obj.declare_var(name, options.dtype)

    def evaluate(self, trajectories: ndarray, timestamps: ndarray) -> float:
        # set sampling period
        period = mean(_step_widths(timestamps))
        self.rtamt_obj.set_sampling_period(period, "s", 0.1)

        traces = {"time": timestamps.tolist()}

        for name, options in self.predicates.items():
            traces[name] = trajectories[options.column].tolist()

        robustness = self.rtamt_obj.evaluate(traces)

        return robustness[-1][1]


class RTAMTDense(Specification):
    def __init__(self, phi: str, predicates: Dict[str, Predicate]):
        try:
            from rtamt import STLDenseTimeSpecification
            from rtamt.enumerations.options import Semantics
        except ModuleNotFoundError:
            raise RuntimeError("RTAMT library must be installed to use RTAMT dense time backend")

        self.predicates = {name: predicate.column for name, predicate in predicates.items()}
        self.rtamt_obj = STLDenseTimeSpecification(Semantics.STANDARD)
        self.rtamt_obj.spec = phi
        self.rtamt_obj.parse()
        self.rtamt_obj.pastify()

        for name, options in predicates.items():
            self.rtamt_obj.declare_var(name, options.dtype)

    def evaluate(self, trajectories: ndarray, timestamps: ndarray) -> float:
        column_map = self.predicates.items()
        traces = [
            (name, hstack((timestamps, trajectories[col])).tolist()) for name, col in column_map
        ]

        robustness = self.rtamt_obj.evaluate(*traces)

        return robustness[-1][1]

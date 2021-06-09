from statistics import mean
from typing import (
    Dict,
    Iterable,
    Protocol,
    Literal,
    NamedTuple,
    Sequence,
    Union,
    Tuple,
    runtime_checkable,
)

from numpy import ndarray, array, float32

from .parser import parse


def _parse_traces(trajectories: ndarray, timestamps: ndarray) -> Tuple[ndarray, ndarray]:
    if timestamps.ndim != 1:
        raise ValueError("expected 2-dimensional timestamps")

    if trajectories.ndim == 1 and trajectories.shape[0] == timestamps.shape[0]:
        return array([trajectories]), timestamps
    elif trajectories.ndim == 2:
        if trajectories.shape[0] == timestamps.shape[0]:
            return trajectories.T, timestamps
        elif trajectories.shape[1] == timestamps.shape[0]:
            return trajectories, timestamps
        else:
            raise ValueError(
                "expected trajectories to have one axis of equal length to timestamps"
            )
    else:
        raise ValueError("expected 1 or 2-dimensional trajectories")


@runtime_checkable
class Specification(Protocol):
    def evaluate(self, trajectories: ndarray, timestamps: ndarray) -> float:
        ...


PredicateName = str


class PredicateProps(NamedTuple):
    column: int
    dtype: Literal["float"] = "float"


class TLTK(Specification):
    """TLTk specification backend.

    Attributes:
        phi: The specification requirement
        predicates: A set of Predicate(s) used in the requirement
    """

    def __init__(self, phi: str, predicate_props: Dict[PredicateName, PredicateProps]):
        predicate_names = predicate_props.keys()
        parsed = parse(phi, list(predicate_names))

        if parsed is None:
            raise RuntimeError("Could not parse requirement")

        self.tltk_obj = parsed
        self.props = predicate_props

    def evaluate(self, trajectories: ndarray, timestamps: ndarray) -> float:
        trajectories, timestamps = _parse_traces(trajectories, timestamps)
        prop_map = self.props.items()
        traces = {name: trajectories[props.column].astype(props.dtype) for name, props in prop_map}

        self.tltk_obj.reset()
        self.tltk_obj.eval_interval(traces, timestamps.astype(float32))

        return self.tltk_obj.robustness


def _step_widths(times: Union[Sequence[float], ndarray]) -> Iterable[float]:
    """Compute the distance between adjacent elements."""

    for i in range(len(times) - 2):
        yield abs(times[i] - times[i + 1])


class RTAMTDiscrete(Specification):
    """RTAMT discrete-time specification backend.

    Attributes:
        phi: The specification requirement
        predicates: A set of Predicate(s) used in the requirement
    """

    def __init__(self, phi: str, predicate_props: Dict[PredicateName, PredicateProps]):
        try:
            from rtamt import STLDiscreteTimeSpecification
            from rtamt.enumerations.options import Semantics
        except ModuleNotFoundError:
            raise RuntimeError("RTAMT must be installed to use associated backends")

        if "time" in predicate_props:
            raise ValueError("'time' cannot be used as a predicate name for RTAMT")

        self.rtamt_obj = STLDiscreteTimeSpecification(Semantics.STANDARD)

        self.rtamt_obj.spec = phi
        self.props = {name: props.column for name, props in predicate_props.items()}

        for name, options in predicate_props.items():
            self.rtamt_obj.declare_var(name, options.dtype)

    def evaluate(self, trajectories: ndarray, timestamps: ndarray) -> float:
        trajectories, timestamps = _parse_traces(trajectories, timestamps)
        period = mean(_step_widths(timestamps))
        self.rtamt_obj.set_sampling_period(round(period, 2), "s", 0.1)

        # parse AFTER declaring variables and setting sampling period
        self.rtamt_obj.parse()
        self.rtamt_obj.pastify()

        traces = {"time": timestamps.tolist()}
        for name, column in self.props.items():
            traces[name] = trajectories[column].tolist()

        # traces: Dict['time': timestamps, 'variable'(s): trajectories]
        robustness = self.rtamt_obj.evaluate(traces)

        return robustness[-1][1]


class RTAMTDense(Specification):
    """RTAMT dense-time specification backend.

    Attributes:
        phi: The specification requirement
        predicates: A set of Predicate(s) used in the requirement
    """

    def __init__(self, phi: str, predicate_props: Dict[PredicateName, PredicateProps]):
        try:
            from rtamt import STLDenseTimeSpecification
            from rtamt.enumerations.options import Semantics
        except ModuleNotFoundError:
            raise RuntimeError("RTAMT library must be installed to use RTAMT dense time backend")

        self.rtamt_obj = STLDenseTimeSpecification(Semantics.STANDARD)

        self.props = {name: predicate.column for name, predicate in predicate_props.items()}
        self.rtamt_obj.spec = phi

        for name, options in predicate_props.items():
            self.rtamt_obj.declare_var(name, options.dtype)

    def evaluate(self, trajectories: ndarray, timestamps: ndarray) -> float:
        trajectories, timestamps = _parse_traces(trajectories, timestamps)

        # parse AFTER declaring variables
        self.rtamt_obj.parse()
        self.rtamt_obj.pastify()

        column_map = self.props.items()
        traces = [
            (name, array([timestamps, trajectories[col]]).T.tolist()) for name, col in column_map
        ]

        # traces: List[Tuple[name, List[Tuple[timestamp, trajectory]]]
        robustness = self.rtamt_obj.evaluate(*traces)

        return robustness[-1][1]

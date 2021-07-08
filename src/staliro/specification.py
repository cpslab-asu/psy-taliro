import sys
from statistics import mean
from typing import Dict, NamedTuple, runtime_checkable

if sys.version_info >= (3, 8):
    from typing import Protocol, Literal
else:
    from typing_extensions import Protocol, Literal

if sys.version_info >= (3, 9):
    from collections.abc import Iterable
else:
    from typing import Iterable

from numpy import array, float32

from .parser import parse
from .models import SimulationResult, Timestamps


@runtime_checkable
class Specification(Protocol):
    def evaluate(self, __result: SimulationResult) -> float:
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

    def evaluate(self, result: SimulationResult) -> float:
        trajectories = result.trajectories
        prop_map = self.props.items()
        traces = {name: trajectories[props.column].astype(props.dtype) for name, props in prop_map}

        self.tltk_obj.reset()
        self.tltk_obj.eval_interval(traces, result.timestamps.astype(float32))

        return self.tltk_obj.robustness


def _step_widths(times: Timestamps) -> Iterable[float]:
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
            from rtamt import STLDiscreteTimeSpecification, Semantics
        except ModuleNotFoundError:
            raise RuntimeError("RTAMT must be installed to use associated backends")

        if "time" in predicate_props:
            raise ValueError("'time' cannot be used as a predicate name for RTAMT")

        self.rtamt_obj = STLDiscreteTimeSpecification(Semantics.STANDARD)

        self.rtamt_obj.spec = phi
        self.props = {name: props.column for name, props in predicate_props.items()}

        for name, options in predicate_props.items():
            self.rtamt_obj.declare_var(name, options.dtype)

    def evaluate(self, result: SimulationResult) -> float:
        from rtamt import LTLPastifyException

        self.rtamt_obj.reset()

        period = mean(_step_widths(result.timestamps))
        self.rtamt_obj.set_sampling_period(round(period, 2), "s", 0.1)

        # parse AFTER declaring variables and setting sampling period
        self.rtamt_obj.parse()

        try:
            self.rtamt_obj.pastify()
        except LTLPastifyException:
            pass

        traces = {"time": result.timestamps.tolist()}
        for name, column in self.props.items():
            traces[name] = result.trajectories[column].tolist()

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
            from rtamt import STLDenseTimeSpecification, Semantics
        except ModuleNotFoundError:
            raise RuntimeError("RTAMT library must be installed to use RTAMT dense time backend")

        self.rtamt_obj = STLDenseTimeSpecification(Semantics.STANDARD)

        self.props = {name: predicate.column for name, predicate in predicate_props.items()}
        self.rtamt_obj.spec = phi

        for name, options in predicate_props.items():
            self.rtamt_obj.declare_var(name, options.dtype)

    def evaluate(self, result: SimulationResult) -> float:
        from rtamt import LTLPastifyException

        self.rtamt_obj.reset()

        # parse AFTER declaring variables
        self.rtamt_obj.parse()

        try:
            self.rtamt_obj.pastify()
        except LTLPastifyException:
            pass

        column_map = self.props.items()
        traces = [
            (name, array([result.timestamps, result.trajectories[col]]).T.tolist())
            for name, col in column_map
        ]

        # traces: List[Tuple[name, List[Tuple[timestamp, trajectory]]]
        robustness = self.rtamt_obj.evaluate(*traces)

        return robustness[-1][1]

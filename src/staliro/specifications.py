from __future__ import annotations

import statistics as stats
from abc import ABC, abstractmethod
from typing import Dict, Iterable, Literal, NamedTuple

import numpy as np
from numpy.typing import NDArray

try:
    from rtamt import STLDiscreteTimeSpecification, STLDenseTimeSpecification, Semantics
except:
    _has_rtamt = False
else:
    _has_rtamt = True

from .core import Specification
from .parser import parse

PredicateName = str
PredicateDTypes = Literal["float", "float32", "float64"]


class PredicateProps(NamedTuple):
    column: int
    dtype: PredicateDTypes = "float"


PredicateMap = Dict[PredicateName, PredicateProps]


class StlSpecification(Specification, ABC):
    @abstractmethod
    def __init__(self, requirement: str, predicate_map: PredicateMap):
        ...


class TLTK(StlSpecification):
    """STL logic specification that uses TLTK to compute robustness values.

    Attributes:
        phi: The specification requirement
        predicates: A set of Predicate(s) used in the requirement
    """

    def __init__(self, phi: str, predicate_map: PredicateMap):
        predicate_names = predicate_map.keys()
        parsed = parse(phi, list(predicate_names))

        if parsed is None:
            raise RuntimeError("Could not parse requirement")

        self.tltk_obj = parsed
        self.props = predicate_map

    def evaluate(self, states: NDArray[np.float_], times: NDArray[np.float_]) -> float:
        prop_map = self.props.items()
        traces = {name: states[props.column].astype(props.dtype) for name, props in prop_map}

        self.tltk_obj.reset()
        self.tltk_obj.eval_interval(traces, np.array(times, dtype=np.float32))

        return self.tltk_obj.robustness


def _step_widths(times: NDArray[np.float_]) -> Iterable[float]:
    """Compute the distance between adjacent elements."""

    for i in range(len(times) - 2):
        yield abs(times[i] - times[i + 1])


class RTAMTDiscrete(StlSpecification):
    """STL logic specification that uses RTAMT discrete-time semantics to compute robustness.

    Attributes:
        phi: The specification requirement
        predicates: A set of Predicate(s) used in the requirement
    """

    def __init__(self, phi: str, predicate_map: PredicateMap):
        if not _has_rtamt:
            raise RuntimeError("RTAMT must be installed to use RTAMTDiscrete specification")

        if "time" in predicate_map:
            raise ValueError("'time' cannot be used as a predicate name for RTAMT")

        self.rtamt_obj = STLDiscreteTimeSpecification(Semantics.STANDARD)

        self.rtamt_obj.spec = phi
        self.props = {name: props.column for name, props in predicate_map.items()}

        for name, options in predicate_map.items():
            self.rtamt_obj.declare_var(name, options.dtype)

    def evaluate(self, states: NDArray[np.float_], times: NDArray[np.float_]) -> float:
        from rtamt import LTLPastifyException

        self.rtamt_obj.reset()

        period = stats.mean(_step_widths(times))
        self.rtamt_obj.set_sampling_period(round(period, 2), "s", 0.1)

        # parse AFTER declaring variables and setting sampling period
        self.rtamt_obj.parse()

        try:
            self.rtamt_obj.pastify()
        except LTLPastifyException:
            pass

        traces = {"time": times.tolist()}
        for name, column in self.props.items():
            traces[name] = states[column].tolist()

        # traces: Dict['time': timestamps, 'variable'(s): trajectories]
        robustness = self.rtamt_obj.evaluate(traces)

        return robustness[-1][1]


class RTAMTDense(StlSpecification):
    """STL logic specification that uses RTAMT dense-time semantics to compute robustness.

    Attributes:
        phi: The specification requirement
        predicates: A set of Predicate(s) used in the requirement
    """

    def __init__(self, phi: str, predicate_map: PredicateMap):
        if not _has_rtamt:
            raise RuntimeError("RTAMT must be installed to use RTAMTDense specification")

        self.rtamt_obj = STLDenseTimeSpecification(Semantics.STANDARD)

        self.props = {name: predicate.column for name, predicate in predicate_map.items()}
        self.rtamt_obj.spec = phi

        for name, options in predicate_map.items():
            self.rtamt_obj.declare_var(name, options.dtype)

    def evaluate(self, states: NDArray[np.float_], times: NDArray[np.float_]) -> float:
        from rtamt import LTLPastifyException

        self.rtamt_obj.reset()

        # parse AFTER declaring variables
        self.rtamt_obj.parse()

        try:
            self.rtamt_obj.pastify()
        except LTLPastifyException:
            pass

        column_map = self.props.items()
        traces = [(name, np.array([times, states[col]]).T.tolist()) for name, col in column_map]

        # traces: List[Tuple[name, List[Tuple[timestamp, trajectory]]]
        robustness = self.rtamt_obj.evaluate(*traces)

        return robustness[-1][1]

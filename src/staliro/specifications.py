from __future__ import annotations

from abc import ABC, abstractmethod
from math import inf
from sys import platform
from typing import TYPE_CHECKING, Any, Dict, Iterable, NewType, Optional, Sequence, Tuple, TypeVar

import numpy as np
from attrs import field, frozen
from numpy.typing import NDArray

try:
    from rtamt import Language, Semantics, StlDenseTimeSpecification, StlDiscreteTimeSpecification
except ImportError:
    _has_rtamt = False
else:
    _has_rtamt = True

from .core import Specification, SpecificationError

try:
    from .parser import parse
except:
    _can_parse = False
else:
    _can_parse = True

try:
    from taliro import tptaliro as tp
except ImportError:
    _has_tptaliro = False
else:
    _has_tptaliro = True

try:
    from .parser import SpecificationSyntaxError, TemporalLogic, translate
except ImportError:
    _can_translate = False
else:
    _can_translate = True

if TYPE_CHECKING:
    from taliro.tptaliro import AdjacencyList, Guard, GuardMap, HyDist

StateT = TypeVar("StateT")
PredicateName = str
ColumnT = int
PredicateColumnMap = Dict[PredicateName, ColumnT]


class StlSpecificationException(Exception):
    pass


_Times = NewType("_Times", NDArray[np.float64])
_States = NewType("_States", NDArray[np.float64])
_Parsed = Tuple[_Times, _States]


def _parse_times_states(times: Sequence[float], states: Sequence[Sequence[float]]) -> _Parsed:
    times_ = _Times(np.array(times, dtype=np.float64))
    states_ = _States(np.array(states, dtype=np.float64))

    if times_.ndim != 1:
        raise StlSpecificationException("Times must be a 1-D vector")

    if states_.ndim != 2:
        raise StlSpecificationException("States must be a 2-D matrix")

    if states_.shape[0] == times_.size:
        return (times_, states_.T)
    elif states_.shape[1] == times_.size:
        return (times_, states_)
    else:
        raise StlSpecificationException("States must have one dimension that maches times length")


class StlSpecification(Specification[Sequence[float], float], ABC):
    @abstractmethod
    def __init__(self, requirement: str, column_map: PredicateColumnMap):
        ...

    @property
    def failure_cost(self) -> float:
        return -inf


class TLTK(StlSpecification):
    """STL logic specification that uses TLTK to compute robustness values.

    Attributes:
        phi: The specification requirement
        predicates: A set of Predicate(s) used in the requirement
    """

    def __init__(self, phi: str, column_map: PredicateColumnMap):
        if not _can_parse:
            if platform == "linux":
                raise RuntimeError(
                    "TLTK specifications require parsing functionality. Please refer to the documentation for how to enable parsing."
                )
            else:
                raise RuntimeError("TLTK specification is only available on Linux")

        tltk_obj = parse(phi, list(column_map.keys()))

        if tltk_obj is None:
            raise SpecificationError("could not parse formula")

        self.tltk_obj = tltk_obj
        self.column_map = column_map

    def evaluate(self, states: Sequence[Sequence[float]], times: Sequence[float]) -> float:
        times_, states_ = _parse_times_states(times, states)
        map_items = self.column_map.items()
        traces = {name: np.array(states_[column], dtype=np.float64) for name, column in map_items}
        timestamps = np.array(times_, dtype=np.float32)

        self.tltk_obj.reset()
        self.tltk_obj.eval_interval(traces, timestamps)

        return self.tltk_obj.robustness


class RTAMTDiscrete(StlSpecification):
    """STL logic specification that uses RTAMT discrete-time semantics to compute robustness.

    Attributes:
        phi: The specification requirement
        predicates: A set of Predicate(s) used in the requirement
    """

    def __init__(self, phi: str, column_map: PredicateColumnMap):
        if "time" in column_map:
            raise SpecificationError("'time' cannot be used as a predicate name for RTAMT")

        self.phi = phi
        self.column_map = column_map

    def evaluate(self, states: Sequence[Sequence[float]], times: Sequence[float]) -> float:
        if not _has_rtamt:
            raise RuntimeError("RTAMT must be installed to use RTAMTDiscrete specification")

        times_, states_ = _parse_times_states(times, states)

        if times_.size < 2:
            raise RuntimeError("timestamps must have at least two samples to evaluate")

        spec = StlDiscreteTimeSpecification()

        for name in self.column_map:
            spec.declare_var(name, "float")

        period = times[1] - times[0]

        spec.set_sampling_period(round(period, 2), "s", 0.1)
        spec.spec = self.phi
        spec.parse()

        traces = {"time": list(times)}

        for name, column in self.column_map.items():
            traces[name] = list(states[column])

        robustness = spec.evaluate(traces)
        return robustness[0][1]


class RTAMTDense(StlSpecification):
    """STL logic specification that uses RTAMT dense-time semantics to compute robustness.

    Attributes:
        phi: The specification requirement
        predicates: A set of Predicate(s) used in the requirement
    """

    def __init__(self, phi: str, column_map: PredicateColumnMap):
        self.phi = phi
        self.column_map = column_map

    def evaluate(self, states: Sequence[Sequence[float]], times: Sequence[float]) -> float:
        if not _has_rtamt:
            raise RuntimeError("RTAMT must be installed to use RTAMTDense specification")

        times_, states_ = _parse_times_states(times, states)
        spec = StlDenseTimeSpecification()

        for name in self.column_map:
            spec.declare_var(name, "float")

        spec.spec = self.phi
        spec.parse()

        map_items = self.column_map.items()
        traces = [
            (name, np.array([times_.tolist(), states_[column]]).T.tolist())
            for name, column in map_items
        ]

        robustness = spec.evaluate(*traces)
        return robustness[0][1]


@frozen(slots=True)
class TaliroPredicate:
    name: str = field(kw_only=True)
    A: NDArray[np.float_] = field(kw_only=True)
    b: NDArray[np.float_] = field(kw_only=True)
    l: Optional[NDArray[np.float_]] = field(default=None, kw_only=True)

    def as_dict(self) -> Dict[str, Any]:
        pred = {
            "name": self.name,
            "a": np.array(self.A, dtype=np.double, ndmin=2),
            "b": np.array(self.b, dtype=np.double, ndmin=2),
        }

        if self.l:
            pred["l"] = np.array(self.l, dtype=np.double, ndmin=2)

        return pred

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> TaliroPredicate:
        try:
            l = d["l"]
        except KeyError:
            l = None

        return cls(name=d["name"], A=d["a"], b=d["b"], l=l)


class TpTaliro(StlSpecification):
    """TPTL logic specification that uses TP-TaLiRo to compute robustness values.

    Attributes:
        phi: The specification requirement
        predicates: A set of Predicate(s) used in the requirement
    """

    def __init__(self, phi: str, predicate_map: Iterable[TaliroPredicate]):
        if not _has_tptaliro:
            if platform == "linux":
                raise RuntimeError("Py-TaLiRo must be installed to use TP-TaLiRo specification")
            else:
                raise RuntimeError("Py-TaLiRo is only available on Linux")

        if not _can_translate:
            raise RuntimeError("TP-TaLiRo specifications require translation functionality.")

        # translate STL to TPTL; else, assume valid TPTL
        try:
            self.spec = translate(phi, TemporalLogic.STL, TemporalLogic.TPTL)
        except SpecificationSyntaxError:
            self.spec = phi

        self.pmap = [user_dict.as_dict() for user_dict in predicate_map]

    def evaluate(self, states: Sequence[Sequence[float]], times: Sequence[float]) -> float:
        """Compute the euclidean-based robustness

        Attributes:
            states: State trajectories
            times: Timestamps
        """
        times_, states_ = _parse_times_states(times, states)

        robustness: HyDist = tp.tptaliro(
            spec=self.spec,
            preds=self.pmap,
            st=np.array(states_, dtype=np.double, ndmin=2),
            ts=np.array(times_, dtype=np.double, ndmin=2),
            lt=None,
            adj_list=None,
            guards=None,
        )

        return robustness["ds"]

    def hybrid(
        self,
        states: Sequence[Sequence[float]],
        times: Sequence[float],
        locations: Sequence[float],
        graph: AdjacencyList,
        guard_map: GuardMap,
    ) -> HyDist:
        """Compute hybrid-based robustness metric.

        A couple notes regarding the arguments: (1) `locations` is a trajectory
        of active states corresponding to a timestamp; (2) the `guard_map` must
        have an entry for _every_ edge defined in the `graph`. For example, if
        we have the following adjacency list:

        ```text
        A -> B
        A -> A
        ```

        Then, the guard map should contain an entry for the edge (A, B) and the
        edge (A, A). It is not required to add an entry for the edge (B, A) or
        (B, B) (i.e., the graph is nondeterministic).

        Arguments:
            states: State trajectories
            times: Timestamps
            locations: Location trajectories
            graph: Control location graph represented as an adjacency list
            guard_map: Transition criteria for each edge in the graph
        """

        def into_taliro_guard(constraint: Guard) -> Guard:
            return {
                "a": np.array(constraint["a"], dtype=np.double, ndmin=2),
                "b": np.array(constraint["b"], dtype=np.double, ndmin=2),
            }

        for guard, constraint in guard_map.items():
            guard_map[guard] = into_taliro_guard(constraint)

        robustness: HyDist = tp.tptaliro(
            spec=self.spec,
            preds=self.pmap,
            st=np.array(states, dtype=np.double, ndmin=2),
            ts=np.array(times, dtype=np.double, ndmin=2),
            lt=np.array(locations, dtype=np.double, ndmin=2),
            adj_list=graph,
            guards=guard_map,
        )

        return robustness

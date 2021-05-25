from enum import Enum
from typing import Dict, Optional, Union, List

from numpy import ndarray
from tltk_mtl import Predicate

from .parser import parse, StlSpecification


class Subsystem(Enum):
    TLTK = 1
    RTAMT_DISCRETE = 2
    RTAMT_DENSE = 3


class Specification:
    """
    The Specification class implements the facade pattern to enable the
    use of multiple robustness evaluators as subsystems. The current
    subsystems supported are:

    - TLTk: https://bitbucket.org/cps-research/tltk/src/master/
    - RTAMT: https://github.com/nickovic/rtamt
    """

    def __init__(
        self,
        spec: str,
        data: Union[Dict[str, str], Dict[str, Predicate]],
        subsystem: Subsystem = Subsystem.TLTK,
    ) -> None:
        """
        The Specification is initialized with the user-defined specification,
        the selected subsystem, and the data required by selected subsystem.
        """

        self._spec = spec
        self._subsystem = subsystem
        self._data = data
        self._tltk_cache: Optional[StlSpecification] = None

    def data_keys(self) -> List[str]:
        return list(self._data.keys())

    def evaluate(self, traces: Dict[str, ndarray], timestamps: ndarray) -> float:
        """
        The evaluate function evaluates the robustness value based on the
        supplied traces and timestamps data with the selected subsystem.
        """

        if timestamps.ndim != 1:
            raise ValueError("Timestamps is expected to be a 1-dimensional ndarray")

        for key, trace in traces.items():
            if key not in self._data:
                raise ValueError(f"Unknown trace {key}")
            elif len(trace) != timestamps.size:
                raise ValueError("Traces must be of same length as timestamp ndarray")

        if self._subsystem == Subsystem.TLTK:
            return self._tltk_evaluate(traces, timestamps)
        elif self._subsystem == Subsystem.RTAMT_DISCRETE:
            return self._rtamt_discrete_evaluate(traces, timestamps)
        elif self._subsystem == Subsystem.RTAMT_DENSE:
            raise NotImplementedError()

        raise ValueError("Selected subsystem unrecognized.")

    def _tltk_evaluate(self, traces: Dict[str, ndarray], timestamps: ndarray) -> float:
        """
        The _tltk_evaluate function evaluates the robustness value
        utilizing the TLTK robustness evaluator.
        """

        for predicate in self._data.values():
            if not isinstance(predicate, Predicate):
                raise ValueError(
                    "Provided predicates must be TLTK predicates to evaluate with TLTK backend"
                )

        if self._tltk_cache is None:
            phi = parse(self._spec, self._data)  # type: ignore

            if phi is None:
                raise RuntimeError("Could not parse STL formula into TLTK objects")

            self._tltk_cache = phi

        self._tltk_cache.reset()
        self._tltk_cache.eval_interval(traces, timestamps)

        return self._tltk_cache.robustness

    def _rtamt_discrete_evaluate(self, traces: Dict[str, ndarray], timestamps: ndarray) -> float:
        """
        The _rtamt_discrete_evaluate function evaluates the robustness value
        utilizing the RTAMT discrete-time offline monitor.
        """
        try:
            from rtamt import STLDiscreteTimeSpecification
            from rtamt.spec.stl.discrete_time.specification import Semantics  # type: ignore
        except ModuleNotFoundError:
            raise RuntimeError(
                "RTAMT library must be installed to use RTAMT discrete time backend"
            )

        phi = STLDiscreteTimeSpecification()
        phi.name = "RTAMT Discrete-Time Offline Monitor"
        phi.semantics = Semantics.STANDARD

        # set sampling period
        period = 0.0
        for i in range(0, len(timestamps) - 1):
            period = period + (timestamps[i + 1] - timestamps[i])

        period = period / (len(timestamps) - 1)
        phi.set_sampling_period(period, "s", 0.1)

        # declare variables
        for var_name, dtype in self._data.items():
            if not isinstance(dtype, str):
                raise ValueError("dtype must be of type string")

            phi.declare_var(var_name, dtype)

        # set specification
        phi.spec = self._spec

        # parse specification
        phi.parse()
        phi.pastify()

        # build traces data structure
        rtamt_data = {"time": timestamps.tolist(), **traces}

        # calculate robustness
        robustness = phi.evaluate(rtamt_data)

        return (robustness[-1])[1]

    def _rtamt_dense_evaluate(self, traces: Dict[str, ndarray], timestamps: ndarray) -> float:
        """
        The _rtamt_dense_evaluate function evaluates the robustness value
        utilizing the RTAMT dense-time offline monitor.
        """
        try:
            from rtamt import STLDenseTimeSpecification
            from rtamt.spec.stl.discrete_time.specification import Semantics  # type: ignore
        except ModuleNotFoundError:
            raise RuntimeError("RTAMT library must be installed to use RTAMT dense time backend")

        phi = STLDenseTimeSpecification()
        phi.name = "RTAMT Dense-Time Offline Monitor"
        phi.semantics = Semantics.STANDARD

        # declare variables
        for var_name, dtype in self._data.items():
            if not isinstance(dtype, str):
                raise ValueError("dtype must be of type string")

            phi.declare_var(var_name, dtype)

        # set specification
        phi.spec = self._spec

        # parse specification
        phi.parse()
        phi.pastify()

        # build traces data structure
        rtamt_data = [(key, list(zip(timestamps, trace))) for key, trace in traces.items()]

        # calculate robustness
        robustness = phi.evaluate(*rtamt_data)

        return (robustness[-1])[1]

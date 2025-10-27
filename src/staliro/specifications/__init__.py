"""
Evaluate a `Trace` of system states into a cost value.

A specification represents the transformation from a set of timed system states into a cost value.
While this cost value can be arbitrary in theory, in practice the value represents some quality of
the system that can be computed from the states (such as the conformance to a specific property). To
implement a specification inherit from the `Specification` class, which requires a single method
called `evaluate()` that accepts a `Trace` and returns a `staliro.Result` containing the cost value
and additional annotation data. Specifications can also be created by annotating a function with the
`specification` decorator. A function can return either a ``staliro.Result`` or a cost value that
will be wrapped in a ``staliro.Result``.

Examples
--------

::

    from staliro import Result, models, specifications

    class Specification(staliro.Specification[list[float], float, None]):
        def evaluate(self, trace: models.Trace[list[float]]) -> Result[float, None]:
            ...

    @specifications.specification
    def specification(trace: models.Trace[list[float]]) -> float:
        ...

Temporal Logic Specifications
-----------------------------

Specification implementations are provided that can evaluate the output trace of a system using
*Signal Temporal Logic* (STL). STL allows users to express behavioral requirements for the system
using unambiguous formulas which can be used to directly evaluate the trace to test for
conformance. Two STL specifications are provided, dense and discrete, implemented using the RTAMT
library. Both specifications can be constructed by providing a STL formula as a string, and an
optional dictionary mapping the formula variables to column indexes. If the column dictionary is
provided, the specification will expect states to be `Sequence[float]`, and if the dictionary is
omitted then the states are expected to be `dict[str, float]`.

::

    from staliro.specifications import Specification, rtamt

    s1: Specification[dict[str, float], float, None] = rtamt.parse_dense("always (alt >= 0)")
    s2: Specification[Sequence[float], float, None] = rtamt.parse_dense("always (alt >= 0)", {"alt": 0})

    s1: Specification[dict[str, float], float, None] = rtamt.parse_discrete("always (alt >= 0)")
    s2: Specification[Sequence[float], float, None] = rtamt.parse_discrete("always (alt >= 0)", {"alt": 0})
"""

from . import rtamt
from .banquo import Banquo
from .specification import Specification, specification

__all__ = ["Banquo", "Specification", "specification", "rtamt"]

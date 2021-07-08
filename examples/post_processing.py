from __future__ import annotations

from typing import TypeVar

from staliro import staliro
from staliro.models import blackbox, StaticParameters, SignalTimes, SignalValues, BlackboxResult
from staliro.optimizers import UniformRandom
from staliro.options import SignalOptions, Options
from staliro.results import Iteration, Result
from staliro.signals import LinearFactory
from staliro.specification import PredicateProps, TLTK

_RT = TypeVar("_RT")
_IT = TypeVar("_IT", bound=Iteration)


@blackbox()
def system_model(ps: StaticParameters, ts: SignalTimes, ss: SignalValues) -> BlackboxResult:
    pass


class ProcessedResult:
    pass


def post_process(result: Result[_RT, _IT]) -> ProcessedResult:
    return ProcessedResult()


initial_conditions = [(0, 10), (150, 3600), (1.0, 2.0)]
signals = [
    SignalOptions(interval=(0.0, 5.0), factory=LinearFactory()),
]

phi = "always(a <= 10 and b <= 20 and not c >= 1)"
predicates = {
    "a": PredicateProps(0, "float"),
    "b": PredicateProps(1, "float"),
    "c": PredicateProps(2, "float"),
}
spec = TLTK(phi, predicates)

options = Options(runs=1, iterations=10, static_parameters=initial_conditions, signals=signals)

optimizer = UniformRandom()

# Example using the first falsify method where optimizer is passed by value
results = staliro(system_model, spec, optimizer, options)

# Process results after run
processed_results = post_process(results)

print(processed_results)

from __future__ import annotations

from itertools import accumulate
from typing import Iterable, List, Sequence, TypeVar, cast

import numpy as np

from .core.cost import SpecificationOrFactory
from .core.interval import Interval
from .core.model import Model, SignalParameters
from .options import Options, SignalOptions
from .core.optimizer import Optimizer
from .core.result import Result
from .core.scenario import Scenario

RT = TypeVar("RT")
ET = TypeVar("ET")


def _signal_times(options: SignalOptions) -> List[float]:
    if options.signal_times is not None:
        return options.signal_times
    else:
        times_array = np.linspace(
            start=options.bound.lower,
            stop=options.bound.upper,
            num=options.control_points,
            dtype=np.float64,
        )

        return cast(List[float], times_array.tolist())


def _signal_parameters(signals: Sequence[SignalOptions], offset: int) -> List[SignalParameters]:
    control_points = map(lambda s: s.control_points, signals)
    range_starts = accumulate(control_points, initial=offset)
    values_ranges = [slice(start, end) for start, end in zip(range_starts, control_points)]

    def parameters(signal: SignalOptions, values_range: slice) -> SignalParameters:
        return SignalParameters(values_range, _signal_times(signal), signal.factory)

    return [
        parameters(signal, values_range) for signal, values_range in zip(signals, values_ranges)
    ]


def _signal_bounds(signals: Iterable[SignalOptions]) -> List[Interval]:
    return sum(([signal.bound] * signal.control_points for signal in signals), [])


def staliro(
    model: Model[ET],
    specification: SpecificationOrFactory,
    optimizer: Optimizer[RT],
    options: Options,
) -> Result[RT, ET]:
    """Search for falsifying inputs to the provided system.

    Using the optimizer, search the input space defined in the options for cases which falsify the
    provided specification represented by the formula phi and the predicates.

    Args:
        model: The model of the system being tested.
        specification: The requirement for the system.
        optimizer: The optimizer to use to search the sample space.
        options: General options to manipulate the behavior of the search.

    Returns:
        An object containing the result of each optimization attempt.
    """
    static_params_end = len(options.static_parameters)
    signal_parameters = _signal_parameters(options.signals, static_params_end)

    scenario = Scenario(
        model=model,
        specification=specification,
        runs=options.runs,
        iterations=options.iterations,
        seed=options.seed,
        processes=options.process_count,
        bounds=options.static_parameters + _signal_bounds(options.signals),
        interval=options.interval,
        static_parameter_range=slice(0, static_params_end),
        signal_parameters=signal_parameters,
    )

    return scenario.run(optimizer)

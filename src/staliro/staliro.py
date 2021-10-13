from __future__ import annotations

from typing import List, TypeVar

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


def _signal_parameters(options: SignalOptions) -> SignalParameters:
    if options.signal_times is not None:
        times: List[float] = options.signal_times
    else:
        times_array = np.linspace(
            start=options.bound.lower,
            stop=options.bound.upper,
            num=options.control_points,
            dtype=np.float64,
        )
        times = times_array.tolist()

    return SignalParameters(n_points=options.control_points, times=times, factory=options.factory)


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
    signal_parameters = [_signal_parameters(signal) for signal in options.signals]
    signal_bounds: List[Interval] = sum(
        ([signal.bound] * signal.control_points for signal in options.signals), []
    )

    scenario = Scenario(
        model=model,
        specification=specification,
        runs=options.runs,
        iterations=options.iterations,
        seed=options.seed,
        processes=options.process_count,
        bounds=options.static_parameters + signal_bounds,
        interval=options.interval,
        n_static_parameters=len(options.static_parameters),
        signal_parameters=signal_parameters,
    )

    return scenario.run(optimizer)

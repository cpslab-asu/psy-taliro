from __future__ import annotations

from typing import Iterable, List, TypeVar, cast

import numpy as np

from .core.cost import SignalParameters, SpecificationOrFactory, decompose_sample
from .core.interval import Interval
from .core.model import Model, ModelResult
from .core.optimizer import Optimizer
from .core.result import Result
from .core.sample import Sample
from .core.scenario import Scenario
from .options import Options, SignalOptions

StateT = TypeVar("StateT")
ResultT = TypeVar("ResultT")
ExtraT = TypeVar("ExtraT")


def _signal_parameters(options: Options, start_index: int) -> List[SignalParameters]:
    t_span = options.interval
    signal_parameters = []

    for signal in options.signals:
        n_control_points = len(signal.control_points)
        stop_index = start_index + n_control_points
        values_range = slice(start_index, stop_index, 1)

        if signal.signal_times is None:
            times_array = np.linspace(
                t_span.lower, t_span.upper, num=n_control_points, dtype=np.float64
            )
            signal_times = cast(list[float], times_array.tolist())
        else:
            signal_times = signal.signal_times

        parameters = SignalParameters(values_range, signal_times, signal.factory)
        signal_parameters.append(parameters)
        start_index = stop_index

    return signal_parameters


def _signal_bounds(signals: Iterable[SignalOptions]) -> tuple[Interval, ...]:
    return sum((signal.control_points for signal in signals), ())


def staliro(
    model: Model[StateT, ExtraT],
    specification: SpecificationOrFactory[StateT],
    optimizer: Optimizer[ResultT],
    options: Options,
) -> Result[ResultT, ExtraT]:
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
    signal_parameters = _signal_parameters(options, static_params_end)
    signal_bounds = _signal_bounds(options.signals)
    bounds = options.static_parameters + signal_bounds

    scenario: Scenario[StateT, ResultT, ExtraT] = Scenario(
        model=model,
        specification=specification,
        runs=options.runs,
        iterations=options.iterations,
        seed=options.seed,
        processes=options.process_count,
        bounds=bounds,
        interval=options.interval,
        static_parameter_range=slice(0, static_params_end, 1),
        signal_parameters=signal_parameters,
    )

    return scenario.run(optimizer)


def simulate_model(
    model: Model[StateT, ExtraT], options: Options, sample: Sample
) -> ModelResult[StateT, ExtraT]:
    static_range = slice(0, len(options.static_parameters))
    signal_params = _signal_parameters(options, static_range.stop)
    static_inputs, signals = decompose_sample(sample, static_range, signal_params)

    return model.simulate(static_inputs, signals, options.interval)

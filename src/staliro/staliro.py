from __future__ import annotations

from itertools import accumulate
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


def _make_parameters(t_span: Interval, start: int, signal_opts: SignalOptions) -> SignalParameters:
    stop = start + signal_opts.control_points
    values_range = slice(start, stop, 1)

    if signal_opts.signal_times is None:
        times_array = np.linspace(
            start=t_span.lower,
            stop=t_span.upper,
            num=signal_opts.control_points,
            dtype=np.float64,
        )
        signal_times = cast(List[float], times_array.tolist())
    else:
        signal_times = signal_opts.signal_times

    return SignalParameters(values_range, signal_times, signal_opts.factory)


def _signal_parameters(options: Options, start_index: int) -> List[SignalParameters]:
    control_points = [opts.control_points for opts in options.signals]
    signal_start_indices = accumulate(control_points, initial=start_index)

    return [
        _make_parameters(options.interval, start_index, signal_opts)
        for start_index, signal_opts in zip(signal_start_indices, options.signals)
    ]


def _signal_bounds(signals: Iterable[SignalOptions]) -> List[Interval]:
    return sum(([signal.bound] * signal.control_points for signal in signals), [])


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

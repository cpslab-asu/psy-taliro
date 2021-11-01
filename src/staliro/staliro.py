from __future__ import annotations

from typing import Iterable, List, Sequence, TypeVar, cast

import numpy as np

from .core.cost import SpecificationOrFactory, SignalParameters, decompose_sample
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


def _signal_times(options: SignalOptions) -> List[float]:
    if options.signal_times is None:
        times_array = np.linspace(
            start=options.bound.lower,
            stop=options.bound.upper,
            num=options.control_points,
            dtype=np.float64,
        )

        return cast(List[float], times_array.tolist())
    else:
        return options.signal_times


def _accumulate(values: Iterable[int], initial: int) -> Iterable[int]:
    current = initial

    for value in values:
        yield current
        current = current + value

    yield current


def _signal_parameters(opts_seq: Sequence[SignalOptions], offset: int) -> List[SignalParameters]:
    control_points = [opts.control_points for opts in opts_seq]
    range_starts = _accumulate(control_points, initial=offset)
    values_ranges = [
        slice(start, start + length, 1) for start, length in zip(range_starts, control_points)
    ]

    def parameters(opts: SignalOptions, values_range: slice) -> SignalParameters:
        return SignalParameters(values_range, _signal_times(opts), opts.factory)

    return [
        parameters(signal, values_range) for signal, values_range in zip(opts_seq, values_ranges)
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
    signal_parameters = _signal_parameters(options.signals, static_params_end)
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
    signal_params = _signal_parameters(options.signals, static_range.stop)
    static_inputs, signals = decompose_sample(sample, static_range, signal_params)

    return model.simulate(static_inputs, signals, options.interval)

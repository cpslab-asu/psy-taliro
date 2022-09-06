from __future__ import annotations

from typing import Any, Iterable, List, Sequence, TypeVar, cast

import numpy as np
from attr import frozen

from .core.cost import SpecificationOrFactory
from .core.interval import Interval
from .core.layout import SampleLayout
from .core.model import Model, ModelResult
from .core.optimizer import Optimizer
from .core.result import Result
from .core.sample import Sample
from .core.scenario import Scenario
from .core.signal import Signal, SignalFactory
from .options import Options, SignalOptions

StateT = TypeVar("StateT")
CostT = TypeVar("CostT")
ResultT = TypeVar("ResultT")
ExtraT = TypeVar("ExtraT")


class SignalFactoryWrapper:
    def __init__(self, factory: SignalFactory, signal_times: List[float]):
        self.factory = factory
        self.signal_times = signal_times

    def __call__(self, signal_values: Sequence[float]) -> Signal:
        if len(signal_values) != len(self.signal_times):
            raise RuntimeError("not enough values for signal")

        signal = self.factory(self.signal_times, signal_values)

        if not isinstance(signal, Signal):
            raise ValueError("signal factory did not return signal")

        return signal


@frozen(slots=True)
class LayoutParameters:
    static_inputs: Sequence[Any]
    signal_options: Sequence[SignalOptions]
    t_span: Interval


def _create_sample_layout(params: LayoutParameters) -> SampleLayout:
    offset = len(params.static_inputs)
    static_inputs_range = (0, offset)
    signal_ranges_map = {}

    for signal_opts in params.signal_options:
        n_points = len(signal_opts.control_points)
        signal_range = (offset, offset + n_points)
        offset = offset + len(signal_opts.control_points)
        signal_times = signal_opts.signal_times

        if signal_times is None:
            times_array = np.linspace(
                params.t_span.lower,
                params.t_span.upper,
                num=n_points,
                dtype=np.float64,
            )
            signal_times = cast(List[float], times_array.tolist())

        signal_ranges_map[signal_range] = SignalFactoryWrapper(signal_opts.factory, signal_times)

    return SampleLayout(static_inputs_range, signal_ranges_map)


def _signal_bounds(signals: Iterable[SignalOptions]) -> tuple[Interval, ...]:
    return sum((signal.control_points for signal in signals), ())


def staliro(
    model: Model[StateT, ExtraT],
    specification: SpecificationOrFactory[StateT, CostT],
    optimizer: Optimizer[CostT, ResultT],
    options: Options,
) -> Result[ResultT, CostT, ExtraT]:
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
    params = LayoutParameters(options.static_parameters, options.signals, options.interval)
    layout = _create_sample_layout(params)
    signal_bounds = _signal_bounds(options.signals)
    bounds = options.static_parameters + signal_bounds

    scenario: Scenario[StateT, CostT, ResultT, ExtraT] = Scenario(
        model=model,
        specification=specification,
        runs=options.runs,
        iterations=options.iterations,
        seed=options.seed,
        processes=options.process_count,
        bounds=bounds,
        interval=options.interval,
        layout=layout,
    )

    return scenario.run(optimizer)


def simulate_model(
    model: Model[StateT, ExtraT], options: Options, sample: Sample
) -> ModelResult[StateT, ExtraT]:
    params = LayoutParameters(options.static_parameters, options.signals, options.interval)
    layout = _create_sample_layout(params)
    inputs = layout.decompose_sample(sample)

    return model.simulate(inputs, options.interval)

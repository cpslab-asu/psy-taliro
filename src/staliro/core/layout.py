from typing import Any, Callable, Dict, Iterable, Mapping, Sequence, Tuple

from attr import field, frozen

from .model import ModelInputs
from .sample import Sample
from .signal import Signal

SignalConstructor = Callable[[Sequence[float]], Signal]
ConstructorMap = Dict[Tuple[int, int], SignalConstructor]


def _to_static_params(value: Sequence[int]) -> slice:
    return slice(value[0], value[1], 1)


def _to_signals(mapping: Mapping[Tuple[int, int], SignalConstructor]) -> ConstructorMap:
    return dict(mapping)


def _validate_signals(_: Any, attr: Any, signals: ConstructorMap) -> None:
    for (lo, hi) in signals.keys():
        if (hi - lo) < 1:
            raise ValueError("Interval must contain at least one element")


def _signals_from_sample(ctors: ConstructorMap, sample: Sample) -> Iterable[Signal]:
    for (start, end), ctor in ctors.items():
        slice_len = end - start
        sample_range = slice(start, end, 1)
        signal_values = sample[sample_range]

        if len(signal_values) != slice_len:
            raise RuntimeError()

        yield ctor(sample[sample_range])


@frozen(slots=True)
class SampleLayout:
    """Representation of the layout of a sample."""

    static_parameters: slice = field(converter=_to_static_params)
    signals: ConstructorMap = field(converter=_to_signals, validator=_validate_signals)

    def decompose_sample(self, sample: Sample) -> ModelInputs:
        static_parameters = sample[self.static_parameters]
        signals = list(_signals_from_sample(self.signals, sample))

        return ModelInputs(static_parameters, signals)

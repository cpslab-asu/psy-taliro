from __future__ import annotations

import logging
import math
import time
from typing import Any, Callable, Generic, Iterable, Iterator, Sequence, Tuple, TypeVar, Union, cast
from concurrent.futures import ProcessPoolExecutor

from attr import frozen, field
from attr.validators import instance_of, deep_iterable, is_callable

from .model import Model, ModelError, ModelResult, ModelData, Failure
from .interval import Interval
from .optimizer import ObjectiveFn
from .sample import Sample
from .signal import Signal, SignalFactory
from .specification import Specification, SpecificationError

StateT = TypeVar("StateT")
ExtraT = TypeVar("ExtraT")

SpecificationFactory = Callable[[Sample], Specification[StateT]]
SpecificationOrFactory = Union[Specification[StateT], SpecificationFactory[StateT]]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def _slice_length(s: slice) -> int:
    return cast(int, s.stop - s.start // s.step)


@frozen()
class TimingData:
    """Storage class for execution durations of different PSY-TaLiRo components.

    The durations stored in this class are for a single evaluation.

    Attributes:
        model: Run time of model component
        specification: Run time of specification component
    """

    model: float
    specification: float

    @property
    def total(self) -> float:
        """The total duration of all components."""

        return self.model + self.specification


@frozen()
class Evaluation(Generic[ExtraT]):
    """The result of applying the cost function to a sample.

    Attributes:
        cost: The result of using a specification to analyze the output of a model
        sample: The sample provided to the model
        extra: Additional data returned by the model
        timing: Execution durations of each component of the cost function
    """

    cost: float
    sample: Sample
    extra: ExtraT
    timing: TimingData


class EvaluationError(Exception):
    pass


T = TypeVar("T")


def _time(func: Callable[[], T]) -> Tuple[float, T]:
    start_time = time.perf_counter()
    result = func()
    stop_time = time.perf_counter()
    duration = stop_time - start_time

    return duration, result


def _mksignal(sample: Sample, params: SignalParameters) -> Signal:
    signal_values = sample[params.values_range]

    if len(signal_values) != _slice_length(params.values_range):
        raise EvaluationError(
            f"cannot satisfy signal values range {params.values_range} with sample {sample}"
        )

    signal = params.factory(params.times, signal_values)

    if not isinstance(signal, Signal):
        raise EvaluationError(
            f"unknown type {type(signal)} returned from signal factory {params.factory.__class__}"
        )

    return signal


def _result_cost(specification: Specification[StateT], result: ModelResult[StateT, Any]) -> float:
    if isinstance(result, ModelData):
        return specification.evaluate(result.states, result.times)
    elif isinstance(result, Failure):
        return -math.inf

    raise ModelError("unsupported type returned from model")


@frozen(auto_attribs=False)
class SignalParameters:
    values_range: slice = field(validator=instance_of(slice))
    times: Sequence[float] = field(validator=deep_iterable(instance_of(float)))
    factory: SignalFactory = field(validator=is_callable())


def decompose_sample(
    sample: Sample, static_range: slice, params_seq: Sequence[SignalParameters]
) -> Tuple[Sequence[float], Sequence[Signal]]:
    static_parameters = sample[static_range]
    signals = [_mksignal(sample, params) for params in params_seq]

    return static_parameters, signals


@frozen()
class Thunk(Generic[StateT, ExtraT]):
    """Class which represents the deferred evaluation of the cost function.

    A Thunk contains all the necessary information to produce an Evaluation, but does not execute
    the computation until the evaluate method is called (lazy value).

    Attributes:
        sample: The sample generated by the optimizer that is provided to the model
        model: Model instance which represents the system
        specification: Specification instance which represents the requirement
        options: Configuration object that controls the behavior of the Model and Specification
    """

    sample: Sample = field(validator=instance_of(Sample))
    model: Model[StateT, ExtraT]
    _specification: SpecificationOrFactory[StateT]
    interval: Interval
    static_parameter_range: slice
    signal_parameters: Sequence[SignalParameters]

    @property
    def specification(self) -> Specification[StateT]:
        if not callable(self._specification):
            return self._specification

        specification = self._specification(self.sample)

        if not isinstance(specification, Specification):
            raise SpecificationError(f"invalid type {type(specification)} given as specification")

        return specification

    def evaluate(self) -> Evaluation[ExtraT]:
        """Evaluate the sample using the specification and model.

        The computation is the following pipeline:
            sample -> model.simulate(sample) -> specification.evaluate(model_result) -> cost

        Returns:
            An Evaluation instance representing the result of the computation pipeline.
        """

        static_inputs, signals = decompose_sample(
            self.sample,
            self.static_parameter_range,
            self.signal_parameters,
        )
        simulate = lambda: self.model.simulate(static_inputs, signals, self.interval)
        model_duration, model_result = _time(simulate)

        compute_cost = lambda: _result_cost(self.specification, model_result)
        cost_duration, cost = _time(compute_cost)
        timing_data = TimingData(model_duration, cost_duration)

        return Evaluation(cost, self.sample, model_result.extra, timing_data)


@frozen()
class ThunkGenerator(Generic[StateT, ExtraT], Iterable[Thunk[StateT, ExtraT]]):
    """Generate Thunk instances from a collection of samples."""

    samples: Iterable[Sample]
    model: Model[StateT, ExtraT]
    specification: SpecificationOrFactory[StateT]
    interval: Interval
    static_parameter_range: slice
    signal_parameters: Sequence[SignalParameters]

    def __iter__(self) -> Iterator[Thunk[StateT, ExtraT]]:
        for sample in self.samples:
            yield Thunk(
                sample,
                self.model,
                self.specification,
                self.interval,
                self.static_parameter_range,
                self.signal_parameters,
            )


def _evaluate(thunk: Thunk[Any, ExtraT]) -> Evaluation[ExtraT]:
    return thunk.evaluate()


@frozen()
class CostFn(ObjectiveFn, Generic[StateT, ExtraT]):
    """Class which represents the composition of a Model and Specification.

    A Model is responsible for modeling the system and returning a trajectory given a sample, and a
    Specification is responsible for evaluating a system trajectory and returning a value which
    indicates its "goodness". Composing these two components produces a component which can produce
    "goodness" values given a sample.

    Attributes:
        model: Model instance which represents a system
        specification: Specification instance or factory which represents the requirement
        options: Configuration object that controls the behavior of the Model and Specification
        history: List of all evaluations produced by this instance
    """

    model: Model[StateT, ExtraT]
    specification: SpecificationOrFactory[StateT]
    interval: Interval
    static_parameter_range: slice
    signal_parameters: Sequence[SignalParameters]
    history: list[Evaluation[ExtraT]] = field(init=False, factory=list)

    def eval_sample(self, sample: Sample) -> float:
        """Compute the cost of a single sample.

        Args:
            sample: Sample to evaluate

        Returns:
            The sample cost
        """

        logger.debug(f"Evaluating sample {sample}")

        thunk = Thunk(
            sample,
            self.model,
            self.specification,
            self.interval,
            self.static_parameter_range,
            self.signal_parameters,
        )
        evaluation = _evaluate(thunk)

        self.history.append(evaluation)

        return evaluation.cost

    def eval_samples(self, samples: Sequence[Sample]) -> list[float]:
        """Compute the cost of multiple samples sequentially.

        Args:
            samples: Samples to evaluate

        Returns:
            The cost for each sample
        """

        logger.debug(f"Evaluating samples {samples}")

        thunks = ThunkGenerator(
            samples,
            self.model,
            self.specification,
            self.interval,
            self.static_parameter_range,
            self.signal_parameters,
        )
        evaluations = [_evaluate(thunk) for thunk in thunks]

        self.history.extend(evaluations)

        return [evaluation.cost for evaluation in evaluations]

    def eval_samples_parallel(self, samples: Sequence[Sample], processes: int) -> list[float]:
        """Compute the cost of multiple samples in parallel.

        Samples are evaluated row-wise, so each row is considered a different sample.

        Args:
            samples: The samples to evaluate
            processes: Number of processes to use to evaluate the samples

        Returns:
            The cost for each sample.
        """

        logger.debug(f"Evaluating samples {samples} with {processes} processes")

        thunks = ThunkGenerator(
            samples,
            self.model,
            self.specification,
            self.interval,
            self.static_parameter_range,
            self.signal_parameters,
        )

        with ProcessPoolExecutor(max_workers=processes) as executor:
            futures: Iterable[Evaluation[ExtraT]] = executor.map(_evaluate, thunks)
            evaluations = list(futures)

        self.history.extend(evaluations)

        return [evaluation.cost for evaluation in evaluations]

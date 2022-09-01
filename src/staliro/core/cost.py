from __future__ import annotations

import logging
import time
from concurrent.futures import ProcessPoolExecutor
from typing import Callable, Generic, Iterable, Iterator, Sequence, Tuple, TypeVar, Union

from attr import field, frozen
from attr.validators import instance_of

from .interval import Interval
from .layout import SampleLayout
from .model import FailureResult, Model, ModelResult
from .optimizer import ObjectiveFn
from .result import Evaluation, TimingData
from .sample import Sample
from .specification import Specification, SpecificationError

StateT = TypeVar("StateT")
CostT = TypeVar("CostT")
SpecificationFactory = Callable[[Sample], Specification[StateT, CostT]]
SpecificationOrFactory = Union[Specification[StateT, CostT], SpecificationFactory[StateT, CostT]]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class EvaluationError(Exception):
    pass


T = TypeVar("T")


def _time(func: Callable[[], T]) -> Tuple[float, T]:
    start_time = time.perf_counter()
    result = func()
    stop_time = time.perf_counter()
    duration = stop_time - start_time

    return duration, result


ExtraT = TypeVar("ExtraT")


@frozen()
class Thunk(Generic[StateT, CostT, ExtraT]):
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
    _specification: SpecificationOrFactory[StateT, CostT]
    interval: Interval
    layout: SampleLayout

    @property
    def specification(self) -> Specification[StateT, CostT]:
        if not callable(self._specification):
            return self._specification

        specification = self._specification(self.sample)

        if not isinstance(specification, Specification):
            raise SpecificationError(f"invalid type {type(specification)} given as specification")

        return specification

    def evaluate(self) -> Evaluation[CostT, ExtraT]:
        """Evaluate the sample using the specification and model.

        The computation is the following pipeline:
            sample -> model.simulate(sample) -> specification.evaluate(model_result) -> cost

        Returns:
            An Evaluation instance representing the result of the computation pipeline.
        """

        inputs = self.layout.decompose_sample(self.sample)
        simulate = lambda: self.model.simulate(inputs, self.interval)
        model_duration, model_result = _time(simulate)

        if not isinstance(model_result, ModelResult):
            raise EvaluationError(f"Incorrect return type from model {type(model_result)}")

        if isinstance(model_result, FailureResult):
            cost = self.specification.failure_cost
            cost_duration = 0.0
        else:
            trace = model_result.trace
            compute_cost = lambda: self.specification.evaluate(trace.states, trace.times)
        cost_duration, cost = _time(compute_cost)

        timing_data = TimingData(model_duration, cost_duration)

        return Evaluation(cost, self.sample, model_result.extra, timing_data)


@frozen()
class ThunkGenerator(Generic[StateT, CostT, ExtraT], Iterable[Thunk[StateT, CostT, ExtraT]]):
    """Generate Thunk instances from a collection of samples."""

    samples: Iterable[Sample]
    model: Model[StateT, ExtraT]
    specification: SpecificationOrFactory[StateT, CostT]
    interval: Interval
    layout: SampleLayout

    def __iter__(self) -> Iterator[Thunk[StateT, CostT, ExtraT]]:
        for sample in self.samples:
            yield Thunk(
                sample,
                self.model,
                self.specification,
                self.interval,
                self.layout,
            )


@frozen()
class CostFn(Generic[StateT, CostT, ExtraT], ObjectiveFn[CostT]):
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
    specification: SpecificationOrFactory[StateT, CostT]
    interval: Interval
    layout: SampleLayout
    history: list[Evaluation[CostT, ExtraT]] = field(init=False, factory=list)

    def eval_sample(self, sample: Sample) -> CostT:
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
            self.layout,
        )
        evaluation = thunk.evaluate()

        self.history.append(evaluation)

        return evaluation.cost

    def eval_samples(self, samples: Sequence[Sample]) -> list[CostT]:
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
            self.layout,
        )
        evaluations = [thunk.evaluate() for thunk in thunks]

        self.history.extend(evaluations)

        return [evaluation.cost for evaluation in evaluations]

    def eval_samples_parallel(self, samples: Sequence[Sample], processes: int) -> list[CostT]:
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
            self.layout,
        )

        with ProcessPoolExecutor(max_workers=processes) as executor:
            futures: Iterable[Evaluation[CostT, ExtraT]] = executor.map(Thunk.evaluate, thunks)
            evaluations = list(futures)

        self.history.extend(evaluations)

        return [evaluation.cost for evaluation in evaluations]

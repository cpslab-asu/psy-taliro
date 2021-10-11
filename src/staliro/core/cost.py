from __future__ import annotations

import concurrent.futures
import logging
import math
import time
from typing import Any, Callable, Generic, Iterable, Iterator, List, Sequence, TypeVar, Union

from attr import frozen

from .model import Model, SimulationResult, SystemInputs, SystemData, SystemFailure
from ..options import Options
from .optimizer import ObjectiveFn
from .sample import Sample
from .specification import Specification

ET = TypeVar("ET")

SpecificationFactory = Callable[[Sample], Specification]
SpecificationOrFactory = Union[Specification, SpecificationFactory]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


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
class Evaluation(Generic[ET]):
    """The result of applying the cost function to a sample.

    Attributes:
        cost: The result of using a specification to analyze the output of a model
        sample: The sample provided to the model
        extra: Additional data returned by the model
        timing: Execution durations of each component of the cost function
    """

    cost: float
    sample: Sample
    extra: ET
    timing: TimingData


@frozen()
class Thunk(Generic[ET]):
    """Class which represents the deferred evaluation of the cost function.

    A Thunk contains all the necessary information to produce an Evaluation, but does not execute
    the computation until the evaluate method is called (lazy value).

    Attributes:
        sample: The sample generated by the optimizer that is provided to the model
        model: Model instance which represents the system
        specification: Specification instance which represents the requirement
        options: Configuration object that controls the behavior of the Model and Specification
    """

    sample: Sample
    model: Model[ET]
    _specification: SpecificationOrFactory
    options: Options

    @property
    def system_inputs(self) -> SystemInputs:
        return SystemInputs(self.sample, self.options)

    @property
    def specification(self) -> Specification:
        if not callable(self._specification):
            return self._specification

        return self._specification(self.sample)

    def result_cost(self, result: SimulationResult[Any]) -> float:
        if isinstance(result, SystemData):
            return self.specification.evaluate(result.states, result.times)
        elif isinstance(result, SystemFailure):
            return -math.inf

        raise TypeError("unsupported type returned from model")

    def evaluate(self) -> Evaluation[ET]:
        """Evaluate the sample using the specification and model.

        The computation is the following pipeline:
            sample -> model.simulate(sample) -> specification.evaluate(model_result) -> cost

        Returns:
            An Evaluation instance representing the result of the computation pipeline.
        """

        model_start = time.perf_counter()
        model_result = self.model.simulate(self.system_inputs, self.options.interval)
        model_stop = time.perf_counter()

        spec_start = time.perf_counter()
        cost = self.result_cost(model_result)
        spec_stop = time.perf_counter()
        timing_data = TimingData(model_stop - model_start, spec_stop - spec_start)

        return Evaluation(cost, self.sample, model_result.extra, timing_data)


@frozen()
class ThunkGenerator(Generic[ET], Iterable[Thunk[ET]]):
    """Generate Thunk instances from a collection of samples."""

    samples: Iterable[Sample]
    model: Model[ET]
    specification: SpecificationOrFactory
    options: Options

    def __iter__(self) -> Iterator[Thunk[ET]]:
        for sample in self.samples:
            yield Thunk(sample, self.model, self.specification, self.options)


def _evaluate(thunk: Thunk[ET]) -> Evaluation[ET]:
    return thunk.evaluate()


class CostFn(ObjectiveFn, Generic[ET]):
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

    def __init__(self, model: Model[ET], specification: SpecificationOrFactory, options: Options):
        self.model = model
        self.specification = specification
        self.options = options
        self.history: List[Evaluation[ET]] = []

    def eval_sample(self, sample: Sample) -> float:
        """Compute the cost of a single sample.

        Args:
            sample: Sample to evaluate

        Returns:
            The sample cost
        """

        logger.debug(f"Evaluating sample {sample}")

        thunk = Thunk(sample, self.model, self.specification, self.options)
        evaluation = _evaluate(thunk)

        self.history.append(evaluation)

        return evaluation.cost

    def eval_samples(self, samples: Sequence[Sample]) -> List[float]:
        """Compute the cost of multiple samples sequentially.

        Samples are evaluated row-wise, so each row is considered a different sample.

        Args:
            samples: Samples to evaluate

        Returns:
            The cost for each sample
        """

        logger.debug(f"Evaluating samples {samples}")

        thunks = ThunkGenerator(samples, self.model, self.specification, self.options)
        evaluations = [_evaluate(thunk) for thunk in thunks]

        self.history.extend(evaluations)

        return [evaluation.cost for evaluation in evaluations]

    def eval_samples_parallel(self, samples: Sequence[Sample], processes: int) -> List[float]:
        """Compute the cost of multiple samples in parallel.

        Samples are evaluated row-wise, so each row is considered a different sample.

        Args:
            samples: The samples to evaluate
            processes: Number of processes to use to evaluate the samples

        Returns:
            The cost for each sample.
        """

        logger.debug(f"Evaluating samples {samples} with {processes} processes")

        thunks = ThunkGenerator(samples, self.model, self.specification, self.options)

        with concurrent.futures.ProcessPoolExecutor(max_workers=processes) as executor:
            evaluations: Iterable[Evaluation[ET]] = executor.map(_evaluate, thunks)

        self.history.extend(evaluations)

        return [evaluation.cost for evaluation in evaluations]

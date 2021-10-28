from __future__ import annotations

import logging
import time
from concurrent.futures import ProcessPoolExecutor
from itertools import islice
from typing import Any, Callable, Generic, Iterable, Iterator, Optional, Sequence, TypeVar, Union

from attr import Attribute, frozen, field
from attr.validators import deep_iterable, instance_of, optional
from numpy.random import default_rng, Generator

from .cost import CostFn, SpecificationOrFactory, SignalParameters
from .interval import Interval
from .model import Model
from .optimizer import Optimizer
from .result import Result, Run
from .specification import Specification

StateT = TypeVar("StateT")
ResultT = TypeVar("ResultT")
ExtraT = TypeVar("ExtraT")

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@frozen()
class CostFnGenerator(Generic[StateT, ExtraT], Iterator[CostFn[StateT, ExtraT]]):
    """Iterator class that generates new instances of CostFn.

    Attributes:
        model: Model instance representing the system use for simulation
        spec: Specification instance for evaluating system trajectories
        options: Configuration object to control behavior of the model and specification
    """

    model: Model[StateT, ExtraT]
    specification: SpecificationOrFactory[StateT]
    interval: Interval
    static_parameter_range: slice
    signal_parameters: Sequence[SignalParameters]

    def __next__(self) -> CostFn[StateT, ExtraT]:
        return CostFn(
            self.model,
            self.specification,
            self.interval,
            self.static_parameter_range,
            self.signal_parameters,
        )


@frozen()
class Experiment(Generic[StateT, ResultT, ExtraT]):
    """Class that represents a single optimization attempt.

    Attributes:
        cost_fn: CostFn instance that is specific to this optimization attempt
        optimizer: Optimizer instance shared by all optimization attempts
        params: OptimizationParams instance specific to this optimization attempt
    """

    cost_fn: CostFn[StateT, ExtraT]
    optimizer: Optimizer[ResultT]
    bounds: Sequence[Interval]
    iterations: int
    seed: int

    def run(self) -> Run[ResultT, ExtraT]:
        """Execute this optimization attempt.

        Returns:
            A Run instance containing the result from the optimizer, the evaluation history of the
            cost function and the overall duration of the optimization attempt.
        """

        start_time = time.perf_counter()
        result = self.optimizer.optimize(self.cost_fn, self.bounds, self.iterations, self.seed)
        stop_time = time.perf_counter()
        duration = stop_time - start_time

        return Run(result, self.cost_fn.history, duration, self.seed)


@frozen()
class ExperimentGenerator(
    Generic[StateT, ResultT, ExtraT], Iterable[Experiment[StateT, ResultT, ExtraT]]
):
    """Generate experiments from a sequence of cost functions and a random number generator.

    Generated experiments will be created by iterating over the sequence of cost functions. For
    each cost function, a random number is generated by the random number generator which is used as
    the seed for the experiment.

    Attributes:
        cost_fn_generator: A generator that returns a sequence of cost functions
        optimizer: The optimizer to use for each experiment
        bounds: The set of intervals that represents the values to be generated by the optimizer
        iterations: The sample budget for each experiment
        rng: The random number generator used to produce a seed for each experiment
    """

    cost_fns: Iterable[CostFn[StateT, ExtraT]]
    optimizer: Optimizer[ResultT]
    bounds: Sequence[Interval]
    iterations: int
    rng: Generator

    def __iter__(self) -> Iterator[Experiment[StateT, ResultT, ExtraT]]:
        for cost_fn in self.cost_fns:
            yield Experiment(
                cost_fn,
                self.optimizer,
                self.bounds,
                self.iterations,
                self.rng.integers(0, 2 ** 32 - 1),
            )


def _run_experiment(experiment: Experiment[Any, ResultT, ExtraT]) -> Run[ResultT, ExtraT]:
    return experiment.run()


def _slice_length(s: slice) -> int:
    diff: int = s.stop - s.start

    if s.step is None:
        step: int = 1
    else:
        step = s.step

    return diff // step


def _validate_specification(
    _: Any, attr: Attribute[Any], value: SpecificationOrFactory[Any]
) -> None:
    if not isinstance(value, Specification) and not callable(value):
        raise TypeError("specification must be a specification instance or a function")


def _validate_static_params(
    inst: Scenario[Any, Any, Any], attr: Attribute[slice], value: slice
) -> None:
    if _slice_length(inst.static_parameter_range) > len(inst.bounds):
        raise ValueError("static parameter range is greater than the number of bounds")


ParamSeq = Sequence[SignalParameters]


def _validate_signal_params(
    inst: Scenario[Any, Any, Any], _: Attribute[ParamSeq], value: ParamSeq
) -> None:
    static_params_length = _slice_length(inst.static_parameter_range)
    param_lengths = [_slice_length(param_obj.values_range) for param_obj in value]
    total_param_length = sum(param_lengths, static_params_length)

    if total_param_length > len(inst.bounds):
        raise ValueError("signal values range is greater than the number of bounds")


def _greater_than(bound: float) -> Callable[[Any, Attribute[Any], Any], None]:
    def validator(_: Any, attr: Attribute[Any], value: Any) -> None:
        if float(value) <= bound:
            raise ValueError(f"{attr.name} must be greater than {bound}")

    return validator


def _within_range(lower: float, upper: float) -> Callable[[Any, Attribute[Any], Any], None]:
    def validator(_: Any, attr: Attribute[Any], value: Any) -> None:
        if not lower <= value <= upper:
            raise ValueError(f"{attr.name} must be inside interval [{lower}, {upper}]")

    return validator


def _min_length(length: int) -> Callable[[Any, Attribute[Any], Any], None]:
    def validator(_: Any, attr: Attribute[Sequence[Any]], value: Sequence[Any]) -> None:
        if len(value) < length:
            raise ValueError(f"{attr.name} must have minimum length of {length}")

    return validator


def _subclass_of(
    class_t: Union[type, tuple[type, ...]]
) -> Callable[[Any, Attribute[Any], Any], None]:
    def validator(_: Any, attr: Attribute[Any], value: Any) -> None:
        if not issubclass(type(value), class_t):
            raise TypeError(f"Expected {attr.name} to have type {class_t}. Got {type(value)}")

    return validator


@frozen(auto_attribs=False)
class Scenario(Generic[StateT, ResultT, ExtraT]):
    """Class that represents a set of optimization attempts.

    Optimization attempts can be run sequentially or in parallel. When run in parallel, the same
    optimizer instance is shared between all processes.

    Attributes:
        model: Model instance representing the system to use for simulation
        specification: Specification instance representing the requirement
        options: Configuration object to control the behavior of the model, specification and
                 optimizer
    """

    model: Model[StateT, ExtraT] = field(validator=_subclass_of(Model))
    specification: SpecificationOrFactory[StateT] = field(validator=_validate_specification)
    runs: int = field(validator=[instance_of(int), _greater_than(0)])
    iterations: int = field(validator=[instance_of(int), _greater_than(0)])
    seed: int = field(validator=[instance_of(int), _within_range(0, 2 ** 32 - 1)])
    processes: Optional[int] = field(validator=optional([instance_of(int), _greater_than(0)]))
    bounds: Sequence[Interval] = field(
        validator=deep_iterable(instance_of(Interval), iterable_validator=_min_length(1))
    )
    interval: Interval = field(validator=instance_of(Interval))
    static_parameter_range: slice = field(validator=_validate_static_params)
    signal_parameters: Sequence[SignalParameters] = field(validator=_validate_signal_params)

    def run(self, optimizer: Optimizer[ResultT]) -> Result[ResultT, ExtraT]:
        """Execute all optimization attempts given an optimizer.

        Args:
            optimizer: Optimizer to use for all optimization attempts.

        Returns:
            A list of Run instances representing the outcomes of each optimization attempt.
        """

        logger.debug("Beginning experiment")
        logger.debug(f"{self.runs} runs of {self.iterations} iterations")
        logger.debug(f"Initial seed: {self.seed}")
        logger.debug(f"Parallelization: {self.processes}")

        rng = default_rng(self.seed)
        cost_fns = CostFnGenerator(
            self.model,
            self.specification,
            self.interval,
            self.static_parameter_range,
            self.signal_parameters,
        )
        experiment_gen = ExperimentGenerator(cost_fns, optimizer, self.bounds, self.iterations, rng)
        experiments = islice(experiment_gen, self.runs)

        if self.processes is not None:
            with ProcessPoolExecutor(self.processes) as executor:
                futures: Iterable[Run[ResultT, ExtraT]] = executor.map(_run_experiment, experiments)
                runs = list(futures)
        else:
            runs = [_run_experiment(experiment) for experiment in experiments]

        return Result(runs, self.interval, self.seed, self.processes)


__all__ = ["Scenario"]

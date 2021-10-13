from __future__ import annotations

import concurrent.futures
import logging
import sys
import time
from itertools import islice
from typing import Generic, Iterable, Iterator, Optional, Sequence, TypeVar

from attr import frozen
from numpy.random import default_rng, Generator

from .cost import CostFn, SpecificationOrFactory
from .interval import Interval
from .model import Model, SignalParameters
from .optimizer import Optimizer
from .result import Result, Run

RT = TypeVar("RT")
ET = TypeVar("ET")

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@frozen()
class CostFnGen(Generic[ET], Iterator[CostFn[ET]]):
    """Iterator class that generates new instances of CostFn.

    Attributes:
        model: Model instance representing the system use for simulation
        spec: Specification instance for evaluating system trajectories
        options: Configuration object to control behavior of the model and specification
    """

    model: Model[ET]
    specification: SpecificationOrFactory
    interval: Interval
    static_parameter_range: slice
    signal_parameters: Sequence[SignalParameters]

    def __next__(self) -> CostFn[ET]:
        return CostFn(
            self.model,
            self.specification,
            self.interval,
            self.static_parameter_range,
            self.signal_parameters,
        )


@frozen()
class Experiment(Generic[RT, ET]):
    """Class that represents a single optimization attempt.

    Attributes:
        cost_fn: CostFn instance that is specific to this optimization attempt
        optimizer: Optimizer instance shared by all optimization attempts
        params: OptimizationParams instance specific to this optimization attempt
    """

    cost_fn: CostFn[ET]
    optimizer: Optimizer[RT]
    bounds: Sequence[Interval]
    iterations: int
    seed: int

    def run(self) -> Run[RT, ET]:
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
class ExperimentGenerator(Generic[RT, ET], Iterable[Experiment[RT, ET]]):
    cost_fn_generator: CostFnGen[ET]
    optimizer: Optimizer[RT]
    bounds: Sequence[Interval]
    iterations: int
    rng: Generator

    def __iter__(self) -> Iterator[Experiment[RT, ET]]:
        for cost_fn in self.cost_fn_generator:
            yield Experiment(
                cost_fn,
                self.optimizer,
                self.bounds,
                self.iterations,
                self.rng.integers(0, sys.maxsize),
            )


def _run_experiment(experiment: Experiment[RT, ET]) -> Run[RT, ET]:
    return experiment.run()


@frozen()
class Scenario(Generic[ET]):
    """Class that represents a set of optimization attempts.

    Optimization attempts can be run sequentially or in parallel. When run in parallel, the same
    optimizer instance is shared between all processes.

    Attributes:
        model: Model instance representing the system to use for simulation
        specification: Specification instance representing the requirement
        options: Configuration object to control the behavior of the model, specification and
                 optimizer
    """

    model: Model[ET]
    specification: SpecificationOrFactory
    runs: int
    iterations: int
    seed: int
    processes: Optional[int]
    bounds: Sequence[Interval]
    interval: Interval
    static_parameter_range: slice
    signal_parameters: Sequence[SignalParameters]

    def run(self, optimizer: Optimizer[RT]) -> Result[RT, ET]:
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
        cost_fns = CostFnGen(
            self.model,
            self.specification,
            self.interval,
            self.static_parameter_range,
            self.signal_parameters,
        )
        experiment_generator = ExperimentGenerator(
            cost_fns, optimizer, self.bounds, self.iterations, rng
        )
        experiments = islice(experiment_generator, self.runs)

        if self.processes is not None:
            with concurrent.futures.ProcessPoolExecutor(self.processes) as executor:
                futures: Iterable[Run[RT, ET]] = executor.map(_run_experiment, experiments)
                runs = list(futures)
        else:
            runs = [_run_experiment(experiment) for experiment in experiments]

        return Result(runs, self.seed, self.processes)

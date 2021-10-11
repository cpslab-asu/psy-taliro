from __future__ import annotations

import concurrent.futures
import logging
import sys
import time
from itertools import islice
from typing import Generic, Iterable, Iterator, TypeVar

from numpy.random import default_rng

from .cost import CostFn, SpecificationOrFactory
from .model import Model
from .optimizer import Optimizer, OptimizationParams
from ..options import Options
from .result import Result, Run

RT = TypeVar("RT")
ET = TypeVar("ET")

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class CostFnGen(Generic[ET], Iterator[CostFn[ET]]):
    """Iterator class that generates new instances of CostFn.

    Attributes:
        model: Model instance representing the system use for simulation
        spec: Specification instance for evaluating system trajectories
        options: Configuration object to control behavior of the model and specification
    """

    def __init__(self, model: Model[ET], spec: SpecificationOrFactory, options: Options):
        self.model = model
        self.spec = spec
        self.options = options

    def __next__(self) -> CostFn[ET]:
        return CostFn(self.model, self.spec, self.options)


class OptimizationParamsGen(Iterator[OptimizationParams]):
    """Iterator class that generates new instances of OptimizationParams.

    Upon instantiation, a random number generator is created using the seed value from the options
    object. The generator attribute of each OptimizationParams object created by this class is
    initialized using this class's RNG to generate an integer that serves as the seed for a new RNG.

    Attributes:
        rng: The random number generator used to make new seeds
        bounds: Sequence of intervals use to generate samples
        iterations: Number of samples to generate
        behavior: Search behavior (FALSIFICATION or MINIMIZATION).
    """

    def __init__(self, options: Options):
        self.rng = default_rng(options.seed)
        self.bounds = options.bounds
        self.iterations = options.iterations
        self.behavior = options.behavior

    def __next__(self) -> OptimizationParams:
        return OptimizationParams(
            self.bounds, self.iterations, self.behavior, self.rng.integers(low=0, high=sys.maxsize)
        )


class Experiment(Generic[RT, ET]):
    """Class that represents a single optimization attempt.

    Attributes:
        cost_fn: CostFn instance that is specific to this optimization attempt
        optimizer: Optimizer instance shared by all optimization attempts
        params: OptimizationParams instance specific to this optimization attempt
    """

    def __init__(self, cost_fn: CostFn[ET], optimizer: Optimizer[RT], params: OptimizationParams):
        self.cost_fn = cost_fn
        self.optimizer = optimizer
        self.params = params

    def run(self) -> Run[RT, ET]:
        """Execute this optimization attempt.

        Returns:
            A Run instance containing the result from the optimizer, the evaluation history of the
            cost function and the overall duration of the optimization attempt.
        """

        start_time = time.perf_counter()
        result = self.optimizer.optimize(self.cost_fn, self.params)
        stop_time = time.perf_counter()
        duration = stop_time - start_time

        return Run(result, self.cost_fn.history, duration)


def _run_experiment(experiment: Experiment[RT, ET]) -> Run[RT, ET]:
    return experiment.run()


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

    def __init__(self, model: Model[ET], specification: SpecificationOrFactory, options: Options):
        self.cost_fns = CostFnGen(model, specification, options)
        self.params = OptimizationParamsGen(options)
        self.options = options

    def run(self, optimizer: Optimizer[RT]) -> Result[RT, ET]:
        """Execute all optimization attempts given an optimizer.

        Args:
            optimizer: Optimizer to use for all optimization attempts.

        Returns:
            A list of Run instances representing the outcomes of each optimization attempt.
        """

        logger.debug("Beginning experiment")
        logger.debug(f"{self.options.runs} runs of {self.options.iterations} iterations")
        logger.debug(f"Initial seed: {self.options.seed}")
        logger.debug(f"Parallelization: {self.options.parallelization}")

        fns_and_params = zip(self.cost_fns, self.params)
        experiments = (Experiment(fn, optimizer, params) for fn, params in fns_and_params)
        n_experiments = islice(experiments, self.options.runs)

        if self.options.process_count is not None:
            with concurrent.futures.ProcessPoolExecutor(self.options.process_count) as executor:
                results: Iterable[Run[RT, ET]] = executor.map(_run_experiment, n_experiments)
        else:
            results = map(_run_experiment, n_experiments)

        return Result(list(results), self.options)

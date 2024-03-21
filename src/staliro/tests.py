"""Create and execute system-level tests using either a cost function, or a model and specification.

Tests require 3 components:

- A way to evaluate samples
- A way to generate samples
- Options to customize the behavior of the test

For sample evaluation, you can use either a `Model` and `Specification`, or a more general
`CostFunc`. For sample generation, you will need an `Optimizer`, and to customize the
behavior you will create a `TestOptions` value to define your test parameters and input
space.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from concurrent.futures import Executor, ProcessPoolExecutor, ThreadPoolExecutor
from enum import IntEnum
from logging import Logger, NullHandler, getLogger
from os import cpu_count
from typing import Generic, Literal, TypeVar, cast, overload
from uuid import UUID, uuid4

from attrs import define, field, frozen
from numpy.random import default_rng
from typing_extensions import TypeAlias

from .cost_func import CostFunc, Result, Sample, SampleLike
from .models import Model, Trace
from .optimizers import ObjFunc, Optimizer
from .options import Interval, TestOptions
from .specifications import Specification

_test_logger = getLogger("staliro.test")
_test_logger.addHandler(NullHandler())

_eval_logger = getLogger("staliro.evaluations")
_eval_logger.addHandler(NullHandler())

S = TypeVar("S")
C = TypeVar("C")
R = TypeVar("R")
E = TypeVar("E")
E1 = TypeVar("E1")
E2 = TypeVar("E2")


class TestError(Exception):
    pass


@frozen(slots=True)
class Evaluation(Generic[C, E]):
    """The result of an evaluation of a `Sample` using a `CostFunc`.

    :param sample: The sample that was evaluated
    :param cost: The computed cost of the sample
    :param extra: The annotation data if it was provided
    """

    sample: Sample
    cost: C
    extra: E


def _cost_func_logger() -> Logger:
    logger = getLogger("staliro.evaluations")
    logger.addHandler(NullHandler())

    return logger


@define(slots=True)
class CostFuncWrapper(Generic[C, E], ObjFunc[C]):
    """Wrapper to transform a `CostFunc` into an `ObjFunc`.

    :param func: The cost function to use for sample evaluation
    :param options: Options for decomposing the values generated into the static and signal inputs
    """

    _func: CostFunc[C, E] = field()
    _options: TestOptions = field()
    _evaluations: list[Evaluation[C, E]] = field(init=False, factory=list)

    def eval_sample(self, sample: SampleLike) -> C:
        s = Sample(sample, self._options)

        _eval_logger.debug(f"Evaluating sample: {s.values}")
        result = self._func.evaluate(s)

        if not isinstance(result, Result):
            raise TypeError("Cost function must return value of type Result")

        evaluation = Evaluation(s, result.value, result.extra)
        self._evaluations.append(evaluation)

        return evaluation.cost


@define(slots=True)
class ParallelCostFuncWrapper(CostFuncWrapper[C, E]):
    """Wrapper to transform a `CostFunc` into an `ObjFunc`.

    This wrapper will use an `concurrent.futures.Executor` to evaluate sample batches in parallel.

    :param func: The cost function to use for sample evaluation
    :param options: Options for sample decomposition and executor construction
    :param executor: The executor to use for parallelization
    """

    _executor: Executor = field()

    def eval_samples(self, samples: Iterable[SampleLike]) -> list[C]:
        def eval_sample(sample: Sample) -> Evaluation[C, E]:
            result = self._func.evaluate(sample)

            if not isinstance(result, Result):
                raise TypeError("Cost function must return value of type Result")

            return Evaluation(sample, result.value, result.extra)

        futures = self._executor.map(eval_sample, [Sample(s, self._options) for s in samples])

        evaluations = list(futures)
        self._evaluations.extend(evaluations)

        return [evaluation.cost for evaluation in evaluations]


@frozen(slots=True)
class Run(Generic[R, C, E]):
    """The result of an optimization attempt.

    :param result: The value returned by the optimizer at exit
    :param evaluations: The set of samples and their associated costs evaluated during the run
    """

    result: R
    evaluations: list[Evaluation[C, E]]


Runs: TypeAlias = list[Run[R, C, E]]


@define(slots=True)
class _Parallelization:
    class Kind(IntEnum):
        THREAD = 0
        PROCESS = 1

    count: Literal["cores"] | int
    kind: _Parallelization.Kind

    def executor(self) -> Executor:
        count = cpu_count() if self.count == "cores" else self.count

        if self.kind is _Parallelization.Kind.THREAD:
            return ThreadPoolExecutor(max_workers=count)

        if self.kind is _Parallelization.Kind.PROCESS:
            return ProcessPoolExecutor(max_workers=count)

        raise ValueError("Unknown kind")


@frozen(slots=True)
class _TestContext(Generic[R, C, E]):
    func: CostFunc[C, E] = field()
    optimizer: Optimizer[C, R] = field()
    options: TestOptions = field()
    bounds: list[Interval] = field()
    seed: int = field()
    parallelization: _Parallelization | None = field(default=None)
    id: UUID = field(init=False, factory=uuid4)

    def make_wrapper(self) -> CostFuncWrapper[C, E]:
        if not self.parallelization:
            return CostFuncWrapper(self.func, self.options)

        return ParallelCostFuncWrapper(self.func, self.options, self.parallelization.executor())

    @property
    def params(self) -> Optimizer.Params:
        return Optimizer.Params(
            seed=self.seed,
            budget=self.options.iterations,
            input_bounds=self.bounds,
        )


def _run_context(ctx: _TestContext[R, C, E]) -> Run[R, C, E]:
    _test_logger.debug(f"Beginning run {ctx.id}")

    wrapper = ctx.make_wrapper()
    result = ctx.optimizer.optimize(wrapper, ctx.params)

    _test_logger.debug(f"Finished run {ctx.id}")

    return Run(result, wrapper._evaluations)


def _make_bounds(options: TestOptions) -> list[Interval]:
    bounds = list(options.static_inputs.values())

    for name in options.signals:
        control_points = options.signals[name].control_points

        if isinstance(control_points, dict):
            bounds.extend(control_points.values())
        else:
            bounds.extend(control_points)

    return bounds


@define(slots=True)
class _TestContexts(Generic[R, C, E], Iterable[_TestContext[R, C, E]]):
    func: CostFunc[C, E]
    optimizer: Optimizer[C, R]
    options: TestOptions
    parallelization: _Parallelization | None

    def __iter__(self) -> Iterator[_TestContext[R, C, E]]:
        rng = default_rng(self.options.seed)
        bounds = _make_bounds(self.options)

        if len(bounds) == 0:
            raise ValueError(
                "Must provide at least one static input or at least one signal with at one or more control points"
            )

        for _ in range(self.options.runs):
            yield _TestContext(
                func=self.func,
                optimizer=self.optimizer,
                options=self.options,
                bounds=bounds,
                seed=rng.integers(0, 2**32 - 1),
                parallelization=self.parallelization,
            )


@define(slots=True)
class Test(Generic[R, C, E]):
    """Class representing a test for a system.

    :param func: The cost function to use to evaluate samples
    :param optimizer: The optimizer to use to generate samples
    :param options: The options to customize the behavior of the test
    """

    func: CostFunc[C, E]
    optimizer: Optimizer[C, R]
    options: TestOptions

    def _contexts(self, parallelization: _Parallelization | None) -> _TestContexts[R, C, E]:
        return _TestContexts(self.func, self.optimizer, self.options, parallelization)

    def _run_sequential(self) -> Runs[R, C, E]:
        parallelization: _Parallelization | None = None
        processes = self.options.processes
        threads = self.options.threads

        if processes:
            parallelization = _Parallelization(count=processes, kind=_Parallelization.Kind.PROCESS)
            _test_logger.debug(f"Sample parallelization: kind=Processes, n={processes}")
        elif threads:
            parallelization = _Parallelization(count=threads, kind=_Parallelization.Kind.THREAD)
            _test_logger.debug(f"Sample parallelization: kind=Threads, n={threads}")
        else:
            _test_logger.debug("Sample parallelization: None")

        return [_run_context(ctx) for ctx in self._contexts(parallelization)]

    def _run_parallel(self, nprocs: int) -> Runs[R, C, E]:
        if self.options.processes:
            _test_logger.warning("Using processes for both runs and sample evaluations is supported")

        parallelization: _Parallelization | None = None
        threads = self.options.threads

        if threads:
            parallelization = _Parallelization(count=threads, kind=_Parallelization.Kind.THREAD)
            _test_logger.debug(f"Sample parallelization: kind=Threads, n={threads}")
        else:
            _test_logger.debug("Sample parallelization: None")

        executor = ProcessPoolExecutor(max_workers=nprocs)
        runs = executor.map(_run_context, self._contexts(parallelization))

        return list(runs)

    def run(self, *, processes: Literal["cores", "all"] | int | None = None) -> list[Run[R, C, E]]:
        """Execute the test and a return a `Run` for each optimization attempt.

        If ``processes`` is set to ``'cores'`` and the number of cores for the CPU cannot be
        determined, then the execution will default to sequential.

        :param processes: The number of processes to use to parallelize the runs
        :returns: A list of `Run` values containing the data for each optimization attempt
        """

        _test_logger.debug("Beginning test")
        _test_logger.debug(f"Initial seed: {self.options.seed}")
        _test_logger.debug(f"Run parallelization: {processes}")

        # This check is done here because cpu_count can return None and we want to default to
        # sequential evaluation if we can't determine the number of cpu cores
        if processes == "cores":
            processes = cpu_count()

        if processes is None:
            return self._run_sequential()

        if processes == "all":
            processes = self.options.runs

        return self._run_parallel(processes)


@frozen(slots=True)
class ModelSpecExtra(Generic[S, E1, E2]):
    """Annotation data produced by a `Model` and `Specification` composition.

    :param trace: The `Trace` produced by the model
    :param model: The annotation data from the model
    :param spec: The annotation data from the specification
    """

    trace: Trace[S]
    model: E1
    spec: E2


@define(slots=True)
class ModelSpec(Generic[S, C, E1, E2], CostFunc[C, ModelSpecExtra[S, E1, E2]]):
    """Cost function created by composing a `Model and a `Specification`.

    The annototation data returned when evaluating a `Sample` is a composition of the annotations
    for both the model and specification called `ModelSpecExtra`, which contains the annotation data
    from each component along with the trace produced by the model. Even if both the model and spec
    have no annotation data, a `ModelSpecExtra` value will still be constructed to contain the trace.

    :param model: The model to use to evaluate the sample into a `Trace`
    :param spec: The specification to use to evaluate the trace into a cost value
    """

    model: Model[S, E1]
    spec: Specification[S, C, E2]

    def evaluate(self, sample: Sample) -> Result[C, ModelSpecExtra[S, E1, E2]]:
        model_result = self.model.simulate(sample)

        if not isinstance(model_result, Result):
            raise TypeError("Model must return value of type Result")

        trace = model_result.value
        spec_result = self.spec.evaluate(trace)

        if not isinstance(spec_result, Result):
            raise TypeError("Specification must return value of type Result")

        return Result(
            value=spec_result.value,
            extra=ModelSpecExtra(trace, model_result.extra, spec_result.extra),
        )


@overload
def setup(
    model: Model[S, E1],
    specification: Specification[S, C, E2],
    optimizer: Optimizer[C, R],
    options: TestOptions,
) -> Test[R, C, ModelSpecExtra[S, E1, E2]]:
    ...


@overload
def setup(
    cost_fn: CostFunc[C, E],
    optimizer: Optimizer[C, R],
    options: TestOptions,
    /,
) -> Test[R, C, E]:
    ...


def setup(
    model: Model[S, E1] | CostFunc[C, E],
    specification: Specification[S, C, E2] | Optimizer[C, R],
    optimizer: Optimizer[C, R] | TestOptions,
    options: TestOptions | None = None,
) -> Test[R, C, ModelSpecExtra[S, E1, E2]] | Test[R, C, E]:
    """Create a test using either a `CostFunc`, or a `Model` and `Specification`.

    :param model: The model or cost function to use to evaluate samples.
    :param specification: The specification to compose with the model, or the `Optimizer` to use to generate samples.
    :param optimizer: The optimizer to use to generate samples or the test options
    :param options: The test options if a model/specification composition was used
    :returns: The configured test containing either the model/specification composition or the cost function
    :raises AssertionError: If provided incorrect types to any parameter
    """

    if options:
        assert isinstance(model, Model)
        assert isinstance(specification, Specification)
        assert isinstance(optimizer, Optimizer)

        return Test(ModelSpec(model, specification), optimizer, options)

    assert isinstance(model, CostFunc)
    assert isinstance(specification, Optimizer)
    assert isinstance(optimizer, TestOptions)

    return Test(model, specification, optimizer)


@overload
def staliro(
    model: Model[S, E1],
    specification: Specification[S, C, E2],
    optimizer: Optimizer[C, R],
    options: TestOptions,
    *,
    processes: Literal["cores", "all"] | int | None = ...,
) -> list[Run[R, C, ModelSpecExtra[S, E1, E2]]]:
    ...


@overload
def staliro(
    cost_fn: CostFunc[C, E],
    optimizer: Optimizer[C, R],
    options: TestOptions,
    /,
    *,
    processes: Literal["cores", "all"] | int | None = ...,
) -> list[Run[R, C, E]]:
    ...


def staliro(
    model: Model[S, E1] | CostFunc[C, E],
    specification: Specification[S, C, E2] | Optimizer[C, R],
    optimizer: Optimizer[C, R] | TestOptions,
    options: TestOptions | None = None,
    *,
    processes: Literal["cores", "all"] | int | None = None,
) -> list[Run[R, C, ModelSpecExtra[S, E1, E2]]] | list[Run[R, C, E]]:
    """Run a test using either a `CostFunc`, or a `Model` and `Specification`.

    :param model: The model or cost function to use to evaluate samples.
    :param specification: The specification to compose with the model, or the `Optimizer` to use to generate samples.
    :param optimizer: The optimizer to use to generate samples or the test options
    :param options: The test options if a model/specification composition was used
    :returns: A list of `Run` values containing the data for each optimization attempt
    :raises AssertionError: If provided incorrect types to any parameter
    """

    if options:
        ms_test = setup(
            cast(Model[S, E1], model),
            cast(Specification[S, C, E2], specification),
            cast(Optimizer[C, R], optimizer),
            options,
        )

        return ms_test.run(processes=processes)

    cf_test = setup(
        cast(CostFunc[C, E], model),
        cast(Optimizer[C, R], specification),
        cast(TestOptions, optimizer),
    )

    return cf_test.run(processes=processes)

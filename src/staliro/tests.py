from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from os import cpu_count
from typing import Generic, Literal, TypeVar, Union, overload

from attrs import define, frozen
from numpy.random import default_rng
from typing_extensions import TypeAlias

from .cost_func import CostFunc, Result, Sample, SampleLike
from .models import Model, Trace
from .optimizers import ObjFunc, Optimizer
from .options import Interval, TestOptions
from .specifications import Specification

S = TypeVar("S")
C = TypeVar("C")
R = TypeVar("R")
E = TypeVar("E")
E1 = TypeVar("E1")
E2 = TypeVar("E2")


class TestError(Exception):
    pass


@frozen(slots=True)
class ModelSpecExtra(Generic[S, E1, E2]):
    trace: Trace[S]
    model: E1
    spec: E2


class ModelSpec(Generic[S, C, E1, E2], CostFunc[C, ModelSpecExtra[S, E1, E2]]):
    __slots__ = ["model", "spec"]

    def __init__(self, model: Model[S, E1], spec: Specification[S, C, E2]):
        self.model = model
        self.spec = spec

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


@frozen(slots=True)
class Evaluation(Generic[C, E]):
    sample: Sample
    cost: C
    extra: E


class CostFuncWrapper(Generic[C, E], ObjFunc[C]):
    __slots__ = ["_func", "_order", "_options", "_evaluations"]

    def __init__(self, func: CostFunc[C, E], order: Sample.Order, options: TestOptions):
        self._func = func
        self._order = order
        self._options = options
        self._evaluations: list[Evaluation[C, E]] = []

    def eval_sample(self, sample: SampleLike) -> C:
        s = Sample(sample, self._order, self._options)
        result = self._func.evaluate(s)

        if not isinstance(result, Result):
            raise TypeError("Cost function must return value of type Result")

        evaluation = Evaluation(s, result.value, result.extra)
        self._evaluations.append(evaluation)

        return evaluation.cost


class ParallelCostFuncWrapper(CostFuncWrapper[C, E]):
    __slots__ = ["_func", "_order", "_options", "_evaluations", "_executor"]

    def __init__(self, func: CostFunc[C, E], order: Sample.Order, options: TestOptions):
        super().__init__(func, order, options)

        if options.processes is None:
            raise TestError("Parallel cost function requires parallelization to be an int")

        self._executor = ThreadPoolExecutor(options.processes)

    def eval_samples(self, samples: Sequence[SampleLike]) -> list[C]:
        def eval_sample(sample: Sample) -> Evaluation[C, E]:
            result = self._func.evaluate(sample)

            if not isinstance(result, Result):
                raise TypeError("Cost function must return value of type Result")

            return Evaluation(sample, result.value, result.extra)

        futures = self._executor.map(
            eval_sample, [Sample(s, self._order, self._options) for s in samples]
        )

        evaluations = list(futures)
        self._evaluations.extend(evaluations)

        return [evaluation.cost for evaluation in evaluations]


@frozen(slots=True)
class Run(Generic[R, C, E]):
    result: R
    evaluations: list[Evaluation[C, E]]


Runs: TypeAlias = list[Run[R, C, E]]


def _make_order(options: TestOptions) -> Sample.Order:
    return Sample.Order(list(options.static_parameters), list(options.signals))


def _make_bounds(order: Sample.Order, options: TestOptions) -> list[Interval]:
    bounds = [options.static_parameters[name] for name in order.static]

    for name in order.signals:
        bounds.extend(options.signals[name].control_points)

    return bounds


@frozen(slots=True)
class TestContext(Generic[R, C, E]):
    func: CostFunc[C, E]
    optimizer: Optimizer[C, R]
    options: TestOptions
    order: Sample.Order
    bounds: list[Interval]
    seed: int


def _run_context(ctx: TestContext[R, C, E]) -> Run[R, C, E]:
    ps = Optimizer.Params(
        seed=ctx.seed,
        budget=ctx.options.iterations,
        input_bounds=ctx.bounds,
    )

    wrapper = CostFuncWrapper(ctx.func, ctx.order, ctx.options)
    result = ctx.optimizer.optimize(wrapper, ps)

    return Run(result, wrapper._evaluations)


class TestContexts(Generic[R, C, E], Iterable[TestContext[R, C, E]]):
    def __init__(self, func: CostFunc[C, E], opt: Optimizer[C, R], opts: TestOptions):
        self.func = func
        self.optimizer = opt
        self.options = opts

    def __iter__(self) -> Iterator[TestContext[R, C, E]]:
        rng = default_rng(self.options.seed)
        order = _make_order(self.options)
        bounds = _make_bounds(order, self.options)

        for _ in range(self.options.runs):
            yield TestContext(
                func=self.func,
                optimizer=self.optimizer,
                options=self.options,
                order=order,
                bounds=bounds,
                seed=rng.integers(0, 2**32 - 1),
            )


def _run_seq(f: CostFunc[C, E], opt: Optimizer[C, R], opts: TestOptions) -> Runs[R, C, E]:
    return [_run_context(ctx) for ctx in TestContexts(f, opt, opts)]


def _run_par(f: CostFunc[C, E], opt: Optimizer[C, R], opts: TestOptions, n: int) -> Runs[R, C, E]:
    executor = ProcessPoolExecutor(max_workers=n)
    runs = executor.map(_run_context, TestContexts(f, opt, opts))

    return list(runs)


Processes: TypeAlias = Union[Literal["cores", "all"], int, None]


@define(slots=True)
class Test(Generic[R, C, E]):
    func: CostFunc[C, E]
    optimizer: Optimizer[C, R]
    options: TestOptions

    def run(self, *, processes: Processes = None) -> list[Run[R, C, E]]:
        # This check is done here because cpu_count can return None and we want to default to
        # sequential evaluation if we can't determine the number of cpu cores
        if processes == "cores":
            processes = cpu_count()

        if processes is None:
            return _run_seq(self.func, self.optimizer, self.options)

        if processes == "all":
            processes = self.options.runs

        return _run_par(self.func, self.optimizer, self.options, processes)


@overload
def staliro(
    model: Model[S, E1],
    specification: Specification[S, C, E2],
    optimizer: Optimizer[C, R],
    options: TestOptions,
    /,
    *,
    processes: Processes = ...,
) -> list[Run[R, C, ModelSpecExtra[S, E1, E2]]]:
    ...


@overload
def staliro(
    cost_fn: CostFunc[C, E],
    optimizer: Optimizer[C, R],
    options: TestOptions,
    /,
    *,
    processes: Processes = ...,
) -> list[Run[R, C, E]]:
    ...


def staliro(
    model: Model[S, E1] | CostFunc[C, E],
    specification: Specification[S, C, E2] | Optimizer[C, R],
    optimizer: Optimizer[C, R] | TestOptions,
    options: TestOptions | None = None,
    /,
    *,
    processes: Processes = None,
) -> list[Run[R, C, ModelSpecExtra[S, E1, E2]]] | list[Run[R, C, E]]:
    if isinstance(model, Model):
        if not isinstance(specification, Specification):
            raise TypeError()

        if not isinstance(optimizer, Optimizer):
            raise TypeError()

        if options is None:
            raise ValueError("Options were not provided")

        return Test(ModelSpec(model, specification), optimizer, options).run(processes=processes)

    if isinstance(model, CostFunc):
        if not isinstance(specification, Optimizer):
            raise TypeError()

        if not isinstance(optimizer, TestOptions):
            raise TypeError()

        return Test(model, specification, optimizer).run(processes=processes)

    raise TypeError("First parameter must be a CostFunc or Model value but found {type(model)}")

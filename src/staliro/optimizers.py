"""
Generate samples for the cost function to evaluate.

An optimizer is responsible for generating the samples that are evaluated by the cost function.
From the evaluation of each sample the ``Optimizer`` recieves a cost value, which represents some
quality of the sample that should either be minimized or maximized. Samples should be generated
until some stopping condition is reached, either from the budget being exhausted or the cost of a
sample meets some criterion. You can create an optimizer by inheriting from the `Optimizer` class,
which has one required method called `optimize()` that should accept as input an `ObjFunc` function
to use for sample evaluation, and a `Optimizer.Params` value containing the optimization parameters
like the budget and initial seed. You can also construct an optimizer by decorating a function with
the `optimizer()` decorator. The decorated function should accept the sample inputs as the
``optimize()`` method.

::

    from staliro import optimizers

    class Optimizer(optimizers.Optimizer[float, None]):
        def optimize(self, func: optimizers.ObjFunc[float], params: optimizers.Optimizer.Params) -> None:
            ...


    @optimizers.optimizer()
    def optimizer(func: optimizers.ObjFunc[float], params: optimizers.Optimizer.Params) -> None:
        ...


Uniform Random
--------------

This module provides the `UniformRandom` optimizer, which uniformly samples the input space.
You can configure the optimizer to exit early if a cost threshold is reached by providing the
``min_cost`` argument to the constructor. This optimizer has no requirements about the type
of the cost value so long as, if a ``min_cost`` is provided, the value supports comparison.

::

    from staliro.optimizers import UniformRandom

    opt = UniformRandom()
    opt = UniformRandom(min_cost=0.0)


Simulated Annealing
-------------------

This module provides the `DualAnnealing` optimizer, which utilizes the general simulated annealing
implementation ``dual_annealing()`` from the SciPy library. When constructing the optimizer, you
can provide a cost threshold using the ``min_cost`` argument to the constructor. The cost values
returned to the optimizer must be `float`.

::

    from staliro.optimizers import DualAnnealing

    opt = DualAnnealing()
    opt = DualAnnealing(min_cost=0.0)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from typing import Generic, Literal, Protocol, TypeVar, overload

from attrs import frozen
from numpy import float_
from numpy.random import Generator, default_rng
from numpy.typing import NDArray
from scipy import optimize
from typing_extensions import TypeAlias

from .cost_func import SampleLike
from .options import Interval

R = TypeVar("R", covariant=True)


class ObjFunc(Protocol[R]):
    """Representation of a function that can be optimized by an optimizer.

    An objective function evaluates samples generated by the optimizer and returns a scalar cost
    value for each sample. The objective function is capable of evaluating one or more samples at
    once.
    """

    def eval_sample(self, sample: SampleLike) -> R:
        """Evaluate a single sample.

        :param sample: The sample to evaluate
        :returns: The cost of the sample
        """

        ...

    def eval_samples(self, samples: Iterable[SampleLike]) -> Sequence[R]:
        """Evaluate a batch of samples.

        :param samples: A sequence of samples to evaluate
        :returns: The cost of each sample in the same order they were given
        """

        return [self.eval_sample(s) for s in samples]


C = TypeVar("C", contravariant=True)


class Optimizer(Generic[C, R], ABC):
    """An optimizer selects samples to be evaluated by the cost function.

    This class is parameterized by two type variables, ``C`` and ``R``. ``C`` is the type of the
    cost value that the optimizer expects to recieve from the cost function, and ``R`` represents
    the type that the optimizer will return at the end of an optimization attempt.
    """

    @frozen(slots=True)
    class Params:
        """The parameters for an optimization attempt.

        :attribute seed: The value to use to seed a random number generator for reproducibility
        :attribute budget: The maximum number of samples to evaluate
        :attribute input_bounds: The search range to for each input variable
        """

        seed: int
        budget: int
        input_bounds: Sequence[Interval]

    @abstractmethod
    def optimize(self, func: ObjFunc[C], params: Params) -> R:
        """Evaluate samples and use the result to select more samples until the budget is reached.

        The optimize method is responsible for generating samples that will be evaluated by the cost
        function into cost values that can be used to inform the selection of subsequent samples. In
        order to recieve cost values, implementations must call either the ``eval_sample`` or
        ``eval_samples`` methods on the ``func`` value.

        :param func: The cost function to use for evaluating samples
        :param params: The optimization parameters
        :returns: The cost value
        """
        ...


Samples: TypeAlias = Iterable[SampleLike]


class Comparable(Protocol):
    @abstractmethod
    def __lt__(self: CT, other: CT) -> bool: ...


CT = TypeVar("CT", bound=Comparable)


def _sample_uniform(bounds: Iterable[Interval], rng: Generator) -> list[float]:
    return [rng.uniform(bound[0], bound[1]) for bound in bounds]


def _minimize(samples: Samples, func: ObjFunc[object]) -> None:
    func.eval_samples(samples)


def _falsify(samples: Samples, func: ObjFunc[CT], min_cost: CT) -> None:
    for sample in samples:
        if func.eval_sample(sample) < min_cost:
            break


class UniformRandom(Optimizer[CT, None]):
    """Optimizer that samples the input space uniformly.

    This optimizer will exhaust the sample budget unless the ``min_cost`` argument is provided. If a
    minimum cost is indicated then the optimizer will terminate early if a cost is found below that
    value.

    :param min_cost: The minimum cost that will cause the optimize to terminate
    """

    def __init__(self, min_cost: CT | None = None):
        self.min_cost = min_cost

    def optimize(self, func: ObjFunc[CT], params: Optimizer.Params) -> None:
        rng = default_rng(params.seed)
        samples = [_sample_uniform(params.input_bounds, rng) for _ in range(params.budget)]

        if self.min_cost:
            return _falsify(samples, func, self.min_cost)

        return _minimize(samples, func)


@frozen(slots=True)
class DualAnnealingResult:
    """Data class containing additional data from a dual annealing optimization.

    :attribute jacobian_value: The value of the cost function jacobian at the minimum cost discovered
    :attribute jacobian_evals: Number of times the jacobian of the cost function was evaluated
    :attribute hessian_value: The value of the cost function hessian as the minimum cost discovered
    :attribute hessian_evals: Number of times the hessian of the cost function was evaluated
    """

    jacobian_value: NDArray[float_] | None
    jacobian_evals: int
    hessian_value: NDArray[float_] | None
    hessian_evals: int


class DualAnnealing(Optimizer[float, DualAnnealingResult]):
    """Optimizer implementing generalized simulated annealing.

    The simulated annealing implementation is provided by the SciPy library dual_annealing function
    with the no_local_search parameter set to True. This optimizer will exhaust the sample budget
    unless the ``min_cost`` argument is provided in the constructor. If ``min_cost`` is provided, then
    the optimizer will exit if a cost value is found that is less than the value.

    :param min_cost: The minimum cost to use as a termination condition
    """

    def __init__(self, min_cost: float | None = None):
        self.min_cost = min_cost

    def optimize(self, func: ObjFunc[float], params: Optimizer.Params) -> DualAnnealingResult:
        def listener(sample: object, cost: float, ctx: Literal[-1, 0, 1]) -> bool:
            if self.min_cost and cost < self.min_cost:
                return True

            return False

        result = optimize.dual_annealing(
            func=lambda x: func.eval_sample(x),
            bounds=list(params.input_bounds),
            seed=params.seed,
            maxfun=params.budget,
            no_local_search=True,  # Disable local search, use only traditional generalized SA
            callback=listener,
        )

        try:
            jac: NDArray[float_] | None = result.jac
            njev = result.njev
        except AttributeError:
            jac = None
            njev = 0

        try:
            hess: NDArray[float_] | None = result.hess
            nhev = result.nhev
        except AttributeError:
            hess = None
            nhev = 0

        return DualAnnealingResult(jac, njev, hess, nhev)


class UserFunc(Protocol[C, R]):
    def __call__(self, __func: ObjFunc[C], __params: Optimizer.Params) -> R: ...


class UserOptimizer(Optimizer[C, R]):
    def __init__(self, func: UserFunc[C, R]):
        self.func = func

    def optimize(self, func: ObjFunc[C], params: Optimizer.Params) -> R:
        return self.func(func, params)


class Decorator(Protocol):
    def __call__(self, __f: UserFunc[C, R]) -> UserOptimizer[C, R]: ...


T = TypeVar("T", covariant=True)
U = TypeVar("U", covariant=True)


@overload
def optimizer(func: UserFunc[C, R]) -> UserOptimizer[C, R]: ...


@overload
def optimizer(func: None = ...) -> Decorator: ...


def optimizer(func: UserFunc[C, R] | None = None) -> UserOptimizer[C, R] | Decorator:
    """Create an `Optimizer` from a function.

    The provided function must accept a `ObjFunc` and a `Optimizer.Params` as arguments. If no
    function is provided, a decorator will be returned that can be called with the function.

    :param func: The function to use as an optimizer
    :returns: An ``Optimizer`` or a decorator to construct an ``Optimizer``
    """

    def _decorator(func: UserFunc[T, U]) -> UserOptimizer[T, U]:
        return UserOptimizer(func)

    return _decorator(func) if func else _decorator

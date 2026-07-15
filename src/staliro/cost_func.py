"""
Evaluate `Sample` values into cost values.

The cost function can be seen as a mapping from a `Sample` into a cost value. The intention is to
produce the values that will be used by the `Optimizer` to select new samples from the input space.
Therefore, each cost value should be some measure of the "quality" of the sample such that
minimizing or maximizing the cost will result in worse/better samples being selected.

Cost functions can be created by either sub-classing the `CostFunc` class or decorating a function
with the `costfunc` decorator.

Examples
--------

.. code-block:: python

    import staliro

    class Func(staliro.CostFunc[float, None]):
        def evaluate(self, sample: staliro.Sample) -> staliro.Result[C, E]:
            ...

    @staliro.costfunc()
    def func(sample: staliro.Sample) -> staliro.Result[C, E]:
        ...
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import UserDict
from typing import Generic, TypeAlias, TypeVar

from attrs import field, frozen

from .optimizers import SampleT
from .signals import Interval, Signal

C = TypeVar("C", covariant=True)
E = TypeVar("E", covariant=True)


@frozen(slots=True)
class Result(Generic[C, E]):
    """A result value containing additional annotation data.

    This class is parameterized by the type variables ``C`` and ``E``, which represent the type of
    the value and the type of the annotation data respectively.

    :param value: The result value
    :param extra: The annotation data value
    """

    value: C
    extra: E


Static: TypeAlias = dict[str, float]


class Signals(UserDict[str, Signal]):
    def __init__(self, signals: dict[str, Signal], tspan: Interval):
        super().__init__(signals)
        self.tspan: Interval = tspan


@frozen(slots=True)
class Inputs(Generic[SampleT]):
    sample: SampleT = field()
    static: Static = field()
    signals: Signals = field()


class CostFunc(ABC, Generic[C, E, SampleT]):
    """The transformation from a `Sample` to a cost value.

    This class is parameterized by two type variables, ``C`` and ``E``. ``C`` is the type of the
    cost returned by this class and the ``value`` attribute in `Result` return value. ``E`` is the
    type of the annotation data in the ``extra`` attribute of the return value.
    """

    @abstractmethod
    def evaluate(self, inputs: Inputs[SampleT]) -> Result[C, E]:
        """Evaluate the given `Sample` into a cost value.

        :param sample: The sample to evaluate
        :returns: The cost value associated with the sample and any provided annotation data
        """

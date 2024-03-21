.. include:: _substitutions.rst

==========
Optimizers
==========

While evaluating samples using either a :doc:`cost function <cost_func>` or a
:doc:`model <models>` and :doc:`specification <specifications>` is important, the generation of the
samples to evaluate is equally important. |psy-taliro| captures the sample generation behavior
as either the :ref:`optimizer <optimizer>` or :ref:`sampler <sampler>` interfaces, which are
expected to select samples for evaluation and accept cost values to inform the selection of further
samples. In principle, sample selection can be entirely independent of the sample evaluation process
but in practice it is valuable to try and minimize/maximize the cost value, which generally
represents some kind of *quality* property of the sample.

.. _obj_func:

Objective Function
------------------

The objective function is the interface through which an optimizer can evaluate generated samples
into cost values. This behavior is encapsulated by the :py:class:`~staliro.optimizers.ObjFunc`
interface, which exposes the :py:meth:`~staliro.optimizers.ObjFunc.eval_sample` and
:py:meth:`~staliro.optimizers.ObjFunc.eval_samples` methods for single and batch sample evaluation
respectively. If the ``parallelization`` option is configured in the :ref:`options <options>`, then
the ``eval_samples()`` method will evaluate the sample batch in parallel according to the number of
threads selected rather than in sequence.

.. _optimizer:

Optimizer
---------

An ``Optimizer`` is a sample generator with *internal* iteration. This means that the optimizer, and
thus the implementer, is responsible for generating samples and calling the objective function to
produce cost values

Base Class
^^^^^^^^^^

You can implement an optimizer by inheriting from the :py:class:`~staliro.optimizers.Optimizer`
class, which has one required method :py:class:`~staliro.optimizers.Optimizer.optimize` that accepts
a :ref:`objective function <obj_func>` and a :py:class:`~staliro.optimizers.Optimizer.Params` value
and returns an arbitrary value representing the result of the optimization attempt. The
``Optimizer[C, R]`` class is parameterized by two type variables: ``C`` represents the cost values
the optimizer expects to operate on, and the ``R`` type variable represents the type of the
optimization result value.

.. code-block:: python

    from dataclasses import dataclass
    from random import Random

    from staliro.optimizers import ObjFunc, Optimizer

    @dataclass()
    class OptResult:
        average: float

    class Opt(Optimizer[float, OptResult]):
        def optimize(self, func: ObjFunc[float], params: Optimizer.Params) -> OptResult:
            rng = Random(params.seed)
            total = 0

            for _ in range(params.budget):
                sample = [rng.uniform(bound[0], bound[1]) for bound in params.bounds]
                cost = func.eval_sample(sample)
                total += cost

            return OptResult(total / params.budget)

Decorator
^^^^^^^^^

Optimizers can also be quickly implemented by decorating a function with the
:py:func:`~staliro.optimizers.optimizer` decorator.

.. code-block:: python

    from staliro.optimizers import ObjFunc, Optimizer, optimizer

    @optimizer()
    def opt(func: ObjFunc[float], params: Optimizer.Params) -> None:
        ...

.. _sampler:

Sampler
-------

.. warning::

    This API is not yet available and may be changed before final release.

The opposite of an :ref:`optimizer <optimizer>` is the ``Sampler`` which is a sample generator
with external iteration. This means that instead of "pushing" samples using the objective function,
the ``Sampler`` accepts requests for samples and is returned cost values.

Base Class
^^^^^^^^^^

The :py:class:`~staliro.optimizers.Sampler` base class can be inherited from, which has a single
required method called :py:class:`~staliro.optimizers.Sampler.sample`, which accepts an optional
cost value and returns a value that can be converted into a :ref:`sample <samples>`. The
``Sampler[C]`` class is parameterized by a single type variable ``C`` which represents the type of
cost value the sampler expects to receive.

.. code-block:: python

    from staliro import SampleLike, optimizers

    class Sampler(optimizers.Sampler[float]):
        def sample(self, cost: float | None = None) -> SampleLike:
            ...

Decorator
^^^^^^^^^

It is also possible to create a ``Sampler`` using the :py:func:`~staliro.optimizers.sampler`
decorator function. However, instead of decorating a plain python function you must apply this
decorator to a `generator function`_ that accepts a
:py:class:`~staliro.optimizers.Optimizer.Params` value, like so:

.. _`generator function`: https://docs.python.org/3/tutorial/classes.html#generators

.. code-block:: python

    from collections.abc import Generator
    from random import Random

    from staliro import SampleLike, optimizers

    @optimizers.sampler()
    def sampler(params: optimizers.Optimizer.Params) -> Generator[SampleLike, float, None]:
        rng = Random(params.seed)

        for _ in range(params.budget):
            sample = [rng.uniform(bound[0], bound[1]) for bound in params.bounds]
            cost = yield sample

.. _uniform-random:

Uniform Random
--------------

The :py:class:`~staliro.optimizers.UniformRandom` optimizer uniformly samples the input space,
ignoring the cost value produced by each sample evaluation when selecting the next sample. The
constructor takes an optional ``min_cost`` parameter which creates a termination condition that
will stop the optimization run if a cost value is encountered that is :math:`\leq min\_cost`. The
type of the cost value must be comparable if a ``min_cost`` is provided.

.. code-block:: python

    from staliro.optimizers import UniformRandom

    opt = UniformRandom()  # Any cost type
    opt = UniformRandom(min_cost=0.0)  # float cost type

Simulated Annealing
-------------------

The :py:class:`~staliro.optimizers.DualAnnealing` optimizer provides an implementation of
`general simulated annealing`_ using the implementation of `dual annealing`_ provided by the SciPy
library. This optimizer expects ``float`` cost values since under the hood the value vectors are
represented using `Numpy`_ ``ndarray`` values. You can optionally provide a ``min_cost`` when
during construction like the :ref:`UniformRandom <uniform-random>` optimizer, which will terminate
the optimization attempt if a cost value is found that is :math:`\leq min\_cost`.

.. _general simulated annealing: https://en.wikipedia.org/wiki/Simulated_annealing
.. _dual annealing: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.dual_annealing.html
.. _Numpy: https://numpy.org

.. code-block:: python

    from staliro.optimizers import DualAnnealing

    opt = DualAnnealing()
    opt = DualAnnealing(min_cost=0.0)

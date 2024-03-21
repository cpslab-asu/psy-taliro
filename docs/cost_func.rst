==============
Cost Functions
==============

A *Cost Function* represents the computation of a *cost* metric from a vector of inputs called
a :py:class:`~staliro.Sample`. In general, a cost function produces some metric value that can be
minimized or maximized depending on the problem space.

.. _samples:

Samples
-------

*Cost Functions* operate over samples, which are vectors of static and signal inputs to the system.
A sample is created by decomposing the vector of ``float`` values produced by the
:py:class:`~staliro.optimizers.Optimizer` based on the inputs declared in the
:py:class:`~staliro.options.TestOptions` object used to run the test. The
:py:attr:`~staliro.Sample.static` attribute on the :py:class:`~staliro.Sample` object provides
access to the set of named static inputs, while the :py:attr:`~staliro.Sample.signals` attribute
allows users to access the named :doc:`signal inputs <signals>`. The :py:obj:`~staliro.SampleLike`
type captures the set of values that can be converted into a ``Sample`` object.

.. _results:

Results
-------

Base Class
----------

The cost function interface is defined in the
:py:class:`CostFunc[C, E] <staliro.cost_func.CostFunc>` class, which users can be extended to create
their own implementations. The type variable ``C`` represents the cost value computed by the
optimizer, and the type variable ``E`` represents the type of the annotation data in the
return value. The only required method to implement is the
:py:meth:`~staliro.cost_func.CostFunc.evaluate` method, which should take as a parameter a
:py:class:`~staliro.Sample` and return a :py:class:`~staliro.Result` value. 

.. code-block:: python
    :linenos:

    from staliro import CostFunc, Sample, Result 


    class Foo(CostFunc[float, str]):
        def __init__(self):
            ...

        def evaluate(self, sample: Sample) -> Result[float, str]:
            ...


    class Bar(CostFunc[tuple[float, float], dict[str, int]]):
        def __init__(self):
            ...

        def evaluate(self, sample: Sample) -> Result[tuple[float, float], dict[str, int]]:
            ...

Decorator
---------

A cost function can also be created by applying the :py:func:`~staliro.cost_func.costfunc` decorator
to a function that accepts a sample and returns a :py:class:`~staliro.Result` value.

.. code-block:: python

    import staliro

    @staliro.costfunc()
    def costfunc(sample: staliro.Sample) -> staliro.Result[float, str]:
        return staliro.Result(value=0.0, extra="foo")

    costfunc.evaluate(...)  # Result(0.0, "foo")

The function can also return a value other than a ``Result``, in which case a new ``Result``
value is created with the ``value`` attribute set to the functions return value and the ``extra``
attribute set to ``None``.

.. code-block:: python

    import staliro

    @staliro.costfunc
    def costfunc(sample: staliro.Sample) -> float:
        return 0.0

    costfunc.evaluate(...)  # Result(0.0, None)


Models
======

A model is used to encapsulate the logic for simulating the system under test (SUT) and producing
a timed set of state values called a ``Trace``. Models can be implemented for just about any system,
regardless of if the system involves solely software, physical hardware, or a distributed set of
services. In general, you would choose to use a model when you already have a way to analyze the
output of a system (like a :doc:`specification <specifications>`) and just need a way to produce
those outputs.

.. _traces:

Traces
------

A :py:class:`~staliro.models.Trace` is a time-annotated set of system states produced by either
directly executing or simulating a system. In this respect, you can imagine a trace as a key-value
mapping between times and system states. You can create a ``Trace`` either by providing the mapping
directly or by providing a set of times and a set of states of equal length.

.. code-block:: Python

    from staliro.models import Trace

    t1 = Trace(times=[1, 2, 3], states=["red", "green", "blue"])
    t2 = Trace({1: "red", 2: "green", 3: "blue"})

.. note::
    
    It is recommended to use keyword arguments when constructing a Trace from times and states for
    readability. If you are using a type-checker, keyword arguments will be enforced.

.. warning::
    
    If you are uncertain about the shape of your data, you should use the :py:func:`len` function
    to ensure that the length of the trace is what you expect.

Results
-------

Models are expected to return an instance of :py:class:`staliro.Result` containing a ``Trace``
value, which can result in longer type annotations and more function calls.

.. code-block:: Python

    from staliro import Result
    from staliro.models import Trace

    r: Result[Trace[list[float]], None]

    r = Result(Trace(times=[], states=[]), None)

To simplify both type annotation and call-sites, you can construct a
:py:class:`models.Result <staliro.models.Result>`, which handles the construction of the inner
``Trace`` while still allowing for annotation data to be provided.

.. code-block:: Python

    from staliro.models import Result

    r: Result[list[float], None]

    r = Result(times=[], states=[], extra=None)
    r = Result({}, None)

Base Class
----------

To implement a model, you must inherit from the :py:class:`~staliro.models.Model` base class. The
only required method is the :py:meth:`~staliro.models.Model.simulate` method which must accept a
:ref:`Sample <samples>` value and return a :ref:`Result <results>` value. A ``Model`` is
parameterized by the type variables ``S`` and ``E`` which represent the type of the state values
produced by the model and the type of the annotation data.

.. code-block:: Python

    from dataclasses import dataclass
    from random import Random

    from staliro import Sample, models

    @dataclass()
    class State:
        """The state of the system under test."""
    
    class Foo(models.Model[State, int]):
        def __init__(self):
            self.rng = Random()

        def simulate(self, sample: Sample) -> models.Result[State, int]:
            return models.Result(
                times=[0, 1, 2],
                states=[State(), State(), State()],
                extra=self.rng.randint(0, 100),
            )

.. _model-decorator:
 
Decorator
---------

For systems that only depend on their input, you can also implement a ``Model`` by decorating a
function with :py:func:`~staliro.models.model`. As with extending the ``Model`` class, decorated
functions must accept a ``Sample`` as a parameter and return a ``staliro.Result`` value.
    
.. code-block:: Python

    from staliro import Sample, models

    @models.model()
    def trace(sample: Sample) -> models.Trace[float]:
        return models.Trace(times=[1.0, 2.0, 3.0], states=[-4.1, 3.2, 100.7])


    @models.model
    def result(sample: Sample) -> models.Result[list[float], str]:
        return models.Result({1.0: [0.1, 4.8, 2.9], 2.0: [-0.5, 3.2, 2.1]}, extra="foo")

Blackbox
--------

A ``Blackbox`` model is similar to the base ``Model`` but instead of recieving the input signals
as a set of continuous functions, it recieves each signal evaluated at a uniformly spaced set of
times. This is most similar to how systems are simulated using `Simulink`_.

.. _Simulink: https://www.mathworks.com/products/simulink.html

.. _blackbox-inputs:

Inputs
^^^^^^

As inputs, a ``Blackbox`` model recieves a
:py:class:`Blackbox.Inputs <staliro.models.Blackbox.Inputs>` value, which contains 2 attributes:
:py:attr:`~staliro.models.Blackbox.Inputs.static` and
:py:attr:`~staliro.models.Blackbox.Inputs.times`. The ``static`` attribute returns the mapping of
names and values for each of the static inputs declared in the :doc:`options <options>`. The
``times`` attribute returns a mapping which contains the evaluation times as keys and a name-value
mapping containing the signal evaluations for the time. The times for the evaluation are uniformly
spaced between the start and end of the ``tspan`` of the options object. If no signals are provided,
then the ``times`` attribute will be empty.

.. code-block:: Python

    from staliro import SignalInput, TestOptions, models

    @models.blackbox()
    def model(inputs: models.Blackbox.Inputs) -> models.Trace[list[float]]:
        x = inputs.static["alpha"] * inputs.static["beta"]
        states = {}

        for time in inputs.times:
            signals = inputs.time[time]
            states[time] = x + signals["rho"] / signals["phi"]

        return models.Trace(states)


    options = TestOptions(
        tspan=(0, 100),
        static_inputs={
            "alpha": (100, 200),
            "beta": (0.0, 1.0),
        },
        signals={
            "rho": SignalInput(control_points=[(0, 10), (10, 20), (20, 30)]),
            "phi": SignalInput(control_points=[(20, 30), (20, 10), (10, 20)]),
        }
    )

.. _blackbox-decorator:

Decorator
^^^^^^^^^

You can construct a ``Blackbox`` model by annotating a Python function with the
:py:func:`~staliro.models.blackbox` decorator. The ``blackbox()`` decorator accepts an optional
``step_size`` parameter which specifies the duration between each evaluation time (and by
consequence the number of evaluation times).

.. code-block:: Python
    
    import staliro.models as models

    @models.blackbox()
    def no_step(inputs: models.Blackbox.Inputs) -> models.Result[object, None]:
        ...

    @models.blackbox(step_size=0.5)
    def with_step(inputs: models.Blackbox.Inputs) -> models.Trace[object]:
        ...

ODE
---

Some systems can be defined in terms of `ordinary differential equations`_ (ODE), which are
functions that return the derivative of the system given the current state of the system. In general
these systems are simulated using integration techniques that for a given initial state will
iteratively evaluate the derivative returned by the ODE to produce a new state that is used in the
next integration step. The implementation of this model relies on the ``solve_ivp()`` method from
the SciPy `integrate`_ module.

.. _ordinary differential equations: https://en.wikipedia.org/wiki/Ordinary_differential_equation
.. _integrate: https://docs.scipy.org/doc/scipy/reference/integrate.html

.. _ode-inputs:

Inputs
^^^^^^

ODE models are expected accept a :py:class:`Ode.Inputs <staliro.models.Ode.Inputs>` value that
has the attributes :py:attr:`time <staliro.models.Ode.Inputs.time>`,
:py:attr:`state <staliro.models.Ode.Inputs.state>`, and
:py:attr:`signals <staliro.models.Ode.Inputs.signals>`. ``time`` is the current time of the
simulation as decided by the integrator. ``state`` is a mapping of names to values that represents
the current state of the simulation. The names in the ``state`` mapping are the names of the static
inputs in the :ref:`options <options>`. Finally, ``signals`` is a name-value mapping that contains
the value of each signal for the current time. The names in the ``signals`` map are the same as the
names of the signals in the options.

.. code-block:: Python

    from staliro import SignalInput, TestOptions, models

    @models.ode()
    def model(inputs: models.Ode.Inputs) -> dict[str, float]:
        alpha_dot = inputs.static["alpha"] * inputs.static["beta"] + inputs.signals["rho"]
        beta_dot = inputs.static["beta"] / inputs.signals["phi"]

        return {"alpha": alpha_dot, "beta": beta_dot}


    options = TestOptions(
        tspan=(0, 100),
        static_inputs={
            "alpha": (100, 200),
            "beta": (0.0, 1.0),
        },
        signals={
            "rho": SignalInput(control_points=[(0, 10), (10, 20), (20, 30)]),
            "phi": SignalInput(control_points=[(20, 30), (20, 10), (10, 20)]),
        }
    )

.. _ode-decorator:

Decorator
^^^^^^^^^

You can construct an ``Ode`` model by annotating a Python function with the
:py:func:`~staliro.models.ode` decorator. The ``ode()`` decorator accepts an optional
``method`` parameter which specifies the integration method to use for simulation.

.. code-block:: Python
    
    import staliro.models as models

    @models.ode()
    def no_method(inputs: models.Ode.Inputs) -> dict[str, float]
        ...

    @models.ode(method="Radau")
    def with_method(inputs: models.Ode.Inputs) -> dict[str, float]:
        ...

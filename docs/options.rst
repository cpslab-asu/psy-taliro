.. include:: _substitutions.rst

=======
Options
=======

|psy-taliro| tests can be customized with by using the :ref:`test options <test-options>`
to modify the testing behavior. When defining :ref:`signal inputs <signal-inputs>` for a test, each
input will require a separate set of options for each particular signal.

.. _intervals:

Many of the options that |psy-taliro| are intervals to represent the range or bounds of a value. 
Each option that accepts an interval, or set of intervals, expects each value to be a sequence
of at least two float values. The first value represents the lower bound and must be strictly less
than the second value, which represents the upper bound. If you are using a PEP484 static type
-checker it should be able to provide hints for the proper types to use. The following are examples
of valid intervals:

.. code-block:: python

    (0.0, 1.0)

    [3.4, 5.1]

The following are examples of invalid or otherwise incorrect intervals:

.. code-block:: python

    (1.0, 1.0)

    [2.3, 4.1, 5.2]

    (3.0, 2.0)

    "12"

.. warning::

    If an interval contains more than two values, the values past the second will be ignored and a
    warning will be printed.

.. _test-options:

Test Options
------------

These options customize the testing behavior and are members of the
:py:class:`~staliro.options.TestOptions` class. This class represents both the input space and
the testing behavior that should be used to analyze the system. Options can be set from either as
constructor arguments, or as attributes on an already constructed options object.

Static Inputs
^^^^^^^^^^^^^

The ``static_inputs`` option configures the set of time-invariant inputs to the system. This option
is a ``dict`` where each key is the input name, and each value is an :ref:`interval <intervals>` for
the valid range of the input.

.. code-block:: python

    from staliro import TestOptions

    opts = TestOptions(
        static_inputs={
            "phi": (0, 10),
            "rho": [10.3, 5.1]
        }
    )

.. _signals:

Signals
^^^^^^^

The search bounds for the set of time-varying inputs to the system. This value for this option
should be a ``dict`` where each key is the signal name and each value is a
:ref:`SignalInput <signal-inputs>`.

.. code-block:: python

    from staliro import TestOptions, SignalInput

    opts = TestOptions(
        signals={
            "alpha": SignalInput(control_points=[(1, 10)]),
        }
    )

Runs
^^^^

The number of optimization attempts to perform. This roughly equates to how many times the
:doc:`optimizer <optimizers>` ``evaluate()`` method is called. The length of the output list
when calling the :py:func:`~staliro.staliro` function will be equal to this number.

.. note::

    The value of this option must be an integer that is greater than or equal to 1.

.. code-block:: python

    from staliro import TestOptions

    TestOptions(runs=100)

Iterations
^^^^^^^^^^

The sample budget for each optimization attempt. This is the maximum number of samples that will be
evaluated before the optimizer exits. For each output :py:class:`~staliro.Run`, this option will
roughly be equivalent to the length of the :py:attr:`~staliro.Run.evaluations` attribute.

.. note::
    
    The value of this option must be an integer that is greater than or equal to 1.

.. code-block:: python

    from staliro import TestOptions

    TestOptions(iterations=500)

Time Span
^^^^^^^^^

The testing time interval. When using :ref:`signal inputs <signal-inputs>` this option is the
interval over which all signals can be evaluated in a model.

.. note::

    This option is required if any :ref:`signals <signals>` are defined. This option may also be
    required by some :doc:`model <models>` or :doc:`cost function <cost_func>` implementations.

.. code-block:: python

    from staliro import TestOptions

    TestOptions(tspan=(0, 100))

Parallelization
^^^^^^^^^^^^^^^

Two options control the parallelization of batch sample evaluation. The first is ``processes`` which
specifies the number of multiple independent child processes to create, while the second is
``threads`` which specifies the number of user threads to create. The primary difference between
these two options is that threads all execute on a single process and their executing is
interleaved, meaning that only a single thread is executing at a time. This is useful when threads
are blocked by things like IO, but it will not speed up computation for CPU bound tasks. For better
CPU throughput, one should use processes instead, which are heavier but capable of true concurrent
execution. The valid values for both of these options are either an integer greater than 0
or ``"cores"`` which will parallelize equal to the number of cores of the machine.

.. note::

    If you use the ``processes`` argument when calling the :py:func:`~staliro.staliro` function
    then you will only be able to parallelize sample evaluation using the ``threads`` option. This
    is because python child processes cannot spawn other child processes.

    If both options are set, if ``processes`` is present in the ``staliro()`` arguments then
    ``threads`` will be used. Otherwise, the ``processes`` option will take precedence.

.. code-block:: python

    from staliro import TestOptions

    TestOptions(threads=10, processes="all")

.. _signal-inputs:

Signal Inputs
-------------

When defining the input :ref:`signals <signals>` for a test, each value needs to be an instance
of the :py:class:`~staliro.signals.SignalInput` class. Each input signal to the cost function is
constructed from the options defined in its ``SignalInput`` object.

Control Points
^^^^^^^^^^^^^^

The valid :ref:`interval <intervals>` for each :ref:`control point <control-points>` to use when
constructing the signal. This option can either be a list of intervals, or a dictionary where
each key is the time associated to the control point and the value is the interval for the control
point.

.. code-block:: python

    from staliro.signals import SignalInput

    SignalInput(control_points=[(10, 20), [30, 31]])

    SignalInput(control_points={0.0: (10, 20), 5.0: (30, 31)})

Factory
^^^^^^^

The :ref:`signal factory <signal-factories>` to use to construct the ``Signal`` value.

.. code-block:: python

    from staliro.signals import SignalInput, piecewise_linear

    SignalInput(factory=piecewise_linear)

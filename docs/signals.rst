.. include:: _substitutions.rst

=======
Signals
=======

In |psy-taliro| signals are continuous, time-varying inputs to a system over a given interval
defined in the :ref:`test options <signals>`.

.. _control-points:

Control Points
--------------

Since it is impossible to randomly generate continuous functions, a signal in |psy-taliro| is
constructed from a set of points called *control points*. These points are fixed values of the
signal at specific moments in time, and the values between each control point are generated
using different interpolation techniques. This allows the approximation of randomly generated
continuous functions, which can be refined to an arbitrary precision by increasing the number
of control points.

Base Class
----------

To implement a custom signal, you can inherit from the :py:class:`~staliro.signals.Signal` class.
This class has only one required method, called :py:meth:`~staliro.signals.Signal.at_time`, and
one method that can be optionally overridden called :py:meth:`~staliro.signals.Signal.at_times`. The
``at_time`` method evaluates the signal for a single time, and the ``at_times`` method evaluates
multiple times. The default ``at_times`` implementation calls the ``at_time`` method for each time
provided, which is sufficient for simple use-cases but users can choose to provide their own
implementations if a more efficient one exists.

.. code-block:: Python

    from collections.abc import Iterable

    from staliro.signals import Signal


    class Constant(Signal):
        def __init__(self, value: float):
            self.constant = value

        def at_time(self, time: float) -> float:
            return self.constant

        def at_times(self, times: Iterable[float]) -> list[float]:
            # This implementation is slightly more efficient because it omits a call to `at_time`
            # for every time in `times`
            return [self.constant for _ in times]


.. _signal-factories:

Factories
---------

In order to provide a custom signal as a system input, you will need to create implement a
:py:class:`~staliro.signals.SignalFactory`, which is a function to create an instance of a signal
for a given set of times and control points. This function can be used for the
:py:attr:`~staliro.signals.SignalInput.factory` attribute of a ``SignalInput``, like so:

.. code-block:: Python

    from staliro import SignalInput, TestOptions


    def constant(times: list[float], control_points: list[float]) -> Constant:
        return Constant(control_points[0])


    options = TestOptions(
        signals={
            "rho": SignalInput(control_points=[(0, 1)], factory=constant)
        }
    )


Basic Signals
-------------

Some basic signal implementations are provided with this library. Most of the provided implementations
are based on interpolators provided by the `SciPy <https://scipy.org>`_ library.

+--------------------+-------------------------------------------------------------------------+
| Name               | Description                                                             |
+====================+=========================================================================+
| |pchip|            | A third-degree cubic hermite spline interpolation.                      |
+--------------------+-------------------------------------------------------------------------+
| |piecewise-linear| | Piecewise interpolation where each control point is connected linearly. |
+--------------------+-------------------------------------------------------------------------+
| |piecewise-const|  | Piecewise interpolation where the function is constant between control  |
|                    | points.                                                                 |
+--------------------+-------------------------------------------------------------------------+
| |harmonic|         | Sum of sinusoidal components with different frequencies/amplitudes.     |
+--------------------+-------------------------------------------------------------------------+

.. |pchip| replace:: :py:func:`~staliro.signals.pchip`
.. |piecewise-linear| replace:: :py:func:`~staliro.signals.piecewise_linear`
.. |piecewise-const| replace:: :py:func:`~staliro.signals.piecewise_constant`
.. |harmonic| replace:: :py:func:`~staliro.signals.harmonic`

Combinators
-----------

This library also provides a set of combinators for modifying the behaviors of other signals.

+--------------------+------------------------------------------------------------------------+
| Name               | Description                                                            |
+====================+========================================================================+
| |clamped|          | Ensure the output of the signal is within the provided bounds.         |
+--------------------+------------------------------------------------------------------------+
| |delayed|          | Shift the time interval of the signal the start after a given amount   |
|                    | of time.                                                               |
+--------------------+------------------------------------------------------------------------+
| |sequenced|        | Given two signals, switch which one is active at a specific time.      |
+--------------------+------------------------------------------------------------------------+

.. |clamped| replace:: :py:func:`~staliro.signals.clamped`
.. |delayed| replace:: :py:func:`~staliro.signals.delayed`
.. |sequenced| replace:: :py:func:`~staliro.signals.sequenced`

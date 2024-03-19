.. include:: _substitutions.rst

========
Examples
========

This page contains some examples of PSY-TaLiRo tests interfacing with different systems. These
examples are also available in the ``example`` directory of the project `repository`_. Each example
will execute a test and create a graph to visualize the outputs.

.. _repository: https://github.com/cpslab-asu/psy-taliro/tree/main/examples

ODE
---

This example defines a model using a basic first-order ODE which represents an aircraft in flight.

.. literalinclude:: ../examples/nonlinear.py
    :language: python
    :linenos:

Blackbox
--------

This example defines a model of the F16 Ground Collision Avoidance System (GCAS) which has been
used to save pilots who have become unresponsive from crashing into the ground. The implementation
of the GCAS system used in this example can be found
`here <https://github.com/stanleybak/AeroBenchVVPython>`_.

.. literalinclude:: ../examples/f16.py
    :language: python
    :linenos:

MATLAB/Simulink
---------------

This example demonstrates executing a simulink model of an automatic transmission. In order to
interface with MATLAB you will need to ensure you have the MATLAB python interface installed
according to the MathWorks
`instructions <https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html>`_.

.. literalinclude:: ../examples/autotrans.py
    :language: python
    :linenos:

Bi-Level
--------

This example demonstrates a bi-level test where the outer optimization attempt searches over the
initial altitude of the aircraft and the inner optimization attempt searches over the initial
attitude of the aircraft.

.. literalinclude:: ../examples/bilevel.py
    :language: python
    :linenos:

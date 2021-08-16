Models
======
The core of S-TaLiRo's system representation is the system model. A system model is a callable object that S-TaLiRo
can evaluate to attempt to find falsifying behavior. 

.. _blackbox:

Blackbox Model
--------------
A blackbox model is the most basic system model because it makes no underlying assumptions about the system under test.
This model requires a delegate function that accepts the static parameter vector X and the signal interpolator vector U,
and returns a tuple of the system states, timestamps and signal values. A blackbox model is responsible for the
simulation of the system and the organization of the output data into the required format. The simulation of the system
can be anything as simple as calling an external application to a complex internal computation.

Blackbox API
------------

.. autoclass:: staliro.models.Blackbox
    :members:
    :undoc-members:

.. _ode:

ODE Model
---------
The ODE model assumes that the function provided returns the change in state of the system rather than a new state. The
return value of this function is integrated over several time intervals to generate new states. This model requires the
delegate function to accept the current time t, the current state vector X and the current input signal value vector U,
and return a state change vector. 

ODE API
-------

.. autoclass:: staliro.models.ODE
    :members:
    :undoc-members:
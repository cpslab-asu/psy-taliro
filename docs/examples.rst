Examples
========

This page contains some examples of PSY-TaLiRo tests interfacing with different systems. Each
test script is displayed and a link to download a zip file containing all the necessary files is
provided.

Python ODE
----------

This example defines a basic first-order ODE which represents an aircraft in flight. This example
requires NumPy and PSY-TaLiRo to be installed.

.. literalinclude:: ../examples/nonlinear.py
    :language: python
    :linenos:

Python Blackbox
---------------

This example executes a model of the F16 GCAS model which has been used to save pilots who have
become unresponsive from crashing into the ground. The GCAS module can be found
`here <https://github.com/stanleybak/AeroBenchVVPython>`_.

.. literalinclude:: ../examples/f16.py
    :language: python
    :linenos:

MATLAB/SimuLink Blackbox
------------------------

This example uses a simulink model of an automatic transmission. In order to interface with MATLAB
you will need to ensure you have the MATLAB python interface installed according to the MathWorks
`instructions <https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html>`_.

.. literalinclude:: ../examples/autotrans.py
    :language: python
    :linenos:

External Blackbox
-----------------

This example interfaces with the PX4 flight control stack and the Gazebo simulator to test drone
behavior.

.. code-block:: python

    # TODO: External blackbox example

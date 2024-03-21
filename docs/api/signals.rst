=======
Signals
=======

.. autoclass:: staliro.signals.Signal
    :members: at_time, at_times

.. autoclass:: staliro.signals.SignalFactory
    :members: __call__

Implementations
---------------

.. autofunction:: staliro.signals.pchip

.. autofunction:: staliro.signals.piecewise_linear

.. autofunction:: staliro.signals.piecewise_constant

.. autofunction:: staliro.signals.harmonic

Combinators
-----------

.. autofunction:: staliro.signals.delayed

.. autofunction:: staliro.signals.clamped

.. autofunction:: staliro.signals.sequenced

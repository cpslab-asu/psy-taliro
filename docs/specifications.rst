.. include:: _substitutions.rst

==============
Specifications
==============

Once a :doc:`model <models>` has been simulated, the output :ref:`trace <traces>` needs to be
evaluated into a cost value, which is captured in the *Specification* interface. In general, a
specification implementation can be any arbitrary function so long as it returns a metic value,
but in the context of |psy-taliro| specifications are generally evaluated in terms of system
requirements expressed using an extension of `Temporal Logic`_ called
*Signal Temporal Logic* (STL).

.. _Temporal Logic: https://en.wikipedia.org/wiki/Temporal_logic#Temporal_logics

.. _signal-temporal-logic:

Introduction to STL
-------------------

STL is higher-order logic that extends `propositional logic`_ (PL) with timed quantifiers, so
instead of evaluating formulas for only a single instant in time we can instead evaluate a formula
over multiple times. This enables us to write formulas to make assertions about some potentially
time-varying properties of a system and verify that the requirement is satisfied as the system
evolves at runtime.

.. _`propositional logic`: https://plato.stanford.edu/entries/logic-propositional/

The most basic building block of a STL formula is the *predicate*, which is an inequality of the
form :math:`\textbf{a} \cdot \textbf{x} \leq b` where the expression
:math:`\textbf{a} \cdot \textbf{x}` is the first-order sum of variables representing the system
state, and :math:`b` is a constant. The following is are some examples of predicates:

.. code-block::
    
    altitude >= 0.0

    flow_rate - drain_rate >= 1.0

    0.5 * brake + 2.0 * throttle <= 2500.0

STL formulas also include operators, which can combine or provide timed quantification of
sub-formulas. The standard PL operators are supported, which are ``Not``, ``And``, ``Or``,
``Implies``, and ``Biconditional``. The most primitive temporal operator introduced by STL is the
``Next`` operator, which asserts that for a given moment, the sub-formula holds at the
following moment. STL also introduces the ``Until`` operator, which is a binary operator that
requires its left sub-formula to hold until the moment before its right sub-formula holds (which
is *required* to hold at some moment in time). From these two operators we can derive the rest of
the temporal operators, which are the following:

``Eventually``
  Unary operator that requires its sub-formula to hold at some moment in time

``Always``
  Unary operator that requires its sub-formula to hold at *all* moments in time

``Release``
  Binary operator that requires its right sub-formula to hold as long as the left sub-formula holds

The table below shows the operators and their common representations in STL formulas, as well as
their *-arity* (how many operands they accept).

+-------------------------+---------------------------------------------------------+-------+
| Operator name           | Representation                                          | Arity |
+=========================+=========================================================+=======+
| And                     | ``and``, ``&&``, or :math:`\wedge`                      | 2     |
+-------------------------+---------------------------------------------------------+-------+
| Or                      | ``or``, ``||``, or :math:`\vee`                         | 2     |
+-------------------------+---------------------------------------------------------+-------+
| Not                     | ``not`` or ``!``, or :math:`\neg`                       | 1     |
+-------------------------+---------------------------------------------------------+-------+
| Implication             | ``implies``, ``->``, or :math:`\rightarrow`             | 2     |
+-------------------------+---------------------------------------------------------+-------+
| Biconditional           | ``<->`` or :math:`\leftrightarrow`                      | 2     |
+-------------------------+---------------------------------------------------------+-------+
| Next [#discrete]_       | ``next``, ``X``, or :math:`\circ`                       | 1     |
+-------------------------+---------------------------------------------------------+-------+
| Eventually [#interval]_ | ``eventually``, ``F``, or :math:`\Diamond`              | 1     |
+-------------------------+---------------------------------------------------------+-------+
| Always [#interval]_     | ``always``, ``G``, or :math:`\square`                   | 1     |
+-------------------------+---------------------------------------------------------+-------+
| Until [#interval]_      | ``until``, ``U``, or :math:`\mathcal{U}`                | 2     |
+-------------------------+---------------------------------------------------------+-------+
| Release [#interval]_    | ``release``, ``R``, or :math:`\mathcal{R}`              | 2     |
+-------------------------+---------------------------------------------------------+-------+

.. rubric:: Notes

.. [#discrete] Only supported for discrete time specifications
.. [#interval] Operator optionally supports an interval written ``OP[t_starts, t_end] ...``. Without
               an interval, an operator applies for all time.

The following are some examples of requirements written using STL:

+------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Requirement                                          | STL representation                                                                                                      |
+======================================================+=========================================================================================================================+
| Do not come in contact with the ground               | ``always (altitude >= 0)``                                                                                              |
+------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Never enter the region                               |                                                                                                                         |
| :math:`[10 \leq x \leq 20] \times [0 \leq y \leq 5]` | :math:`G (not (x \geq 10~and~x \leq 20~and~y \leq 5~and~y \geq 0))`                                                     |
+------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Exit the region 4 seconds after entering it          | :math:`\square ((x\geq 10\wedge x\leq 20\wedge y\leq 5\wedge y\geq 0) \rightarrow                                       |
|                                                      | \Diamond_{[0,4]}~\neg(x\geq 10\wedge x\leq 20\wedge y\leq 5\wedge y\geq 0))`                                            |
+------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+

Base Class
----------

Implementing a *specification* can be accomplished by inheriting from the
:py:class:`~staliro.specifications.Specification` class, which has one required method called
:py:meth:`~staliro.specifications.Specification.evaluate` that accepts a :ref:`Trace <traces>` value
and returns a :ref:`result <results>` containing the *cost* value as well as any additional
annotation data. The ``Specification[S, C, E]`` class is parameterized by 3 type variables: ``S``
represents the type of the system states that the specification expects, ``C`` represents the type
of the cost value returned, and ``E`` represents the type of the annotation data.

.. code-block:: python

    from staliro import Result, Trace
    from staliro.specifications import Specification

    class Spec(Specification[list[float], float, None])
        def evaluate(self, trace: Trace[list[float]]) -> Result[float, None]:
            ...


Decorator
---------

For specifications that only depend on their inputs, you can also use the
:py:func:`~staliro.specifications.specification` decorator to create a ``Specification`` from a
plain Python function.

.. code-block:: python

    from staliro import Result, Trace, specifications

    @specifications.specification()
    def spec(trace: Trace[list[float]]) -> Result[float, None]:
        ...

RTAMT
-----

In order to evaluate a STL formula, a program called a *monitor* is required. One such monitor is
`RTAMT`_, developed by Dejan Nickovic and Tomoya Yamaguchi. Two specification
implementations are provided using this library: :py:class:`~staliro.specifications.RTAMTDiscrete`
and :py:class:`~staliro.specifications.RTAMTDense`. Both specifications accept the same constructor
parameters, which allow users to select the type of state values expected by the optimizer. To
create an instance of either class you must provide a formula written in STL and a dictionary
mapping the variable names in the formula to columns in the state value, which is expected to be a
``list``.

.. _`RTAMT`: https://arxiv.org/abs/2005.11827

.. code-block:: python

    from staliro.models import Trace
    from staliro.optimizers import RTAMTDiscrete

    specification = RTAMTDiscrete("always (alt >= 0)", {"alt": 0})
    states = {
        0.0: [2250.0],
        1.0: [2248.7],
        2.0: [2247.3],
    }

    specification.evaluate(Trace(states))

As an alternative method of construction, you can omit the variable-column mapping which will change
the specification to expect dictionaries containing each variable in the formula.

.. code-block:: python

    from staliro.models import Trace
    from staliro.optimizers import RTAMTDense

    specification = RTAMTDense("always (alt >= 0)")
    states = {
        0.0: {"alt": 2250.0},
        1.0: {"alt": 2248.7},
        2.0: {"alt": 2247.3},
    }

    specification.evaluate(Trace(states))

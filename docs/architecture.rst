.. include:: _substitutions.rst

============
Architecture
============

The following diagram shows the architecture of the |psy-taliro| library. This diagram outlines
the data flow and the connections of the different components as well as identifies which
components can be implemented by users.

.. _architecture_diagram:

.. figure:: _images/architecture.svg

    Architecture diagram of |psy-taliro| library

The following sections contain further discussion of any design decisions.

Components
----------

Each component is represented using a python `Abstract Base Class`_ (ABC), which allows us to test
for sub-class membership so we can ensure that the necessary behavior is satisfied. This approach
was selected over using `Protocol`_ classes or plain functions because protocols define structural
rather than nominal sub-typing (which is harder to enforce), and plain functions are not checkable
beyond testing if they are callable.

.. _Abstract Base Class: https://docs.python.org/3/glossary.html#term-abstract-base-class
.. _Protocol: https://docs.python.org/3/library/typing.html#protocols

.. include:: _substitutions.rst

=======
Caveats
=======

This page discusses any gotchas or considerations that users should keep in mind while implementing
their tests.

Parallelization
---------------

When using multiple processes for parallelization, the cost function (which may contain a model and
specification), the optimizer, and the options object will all need to be communicated across
processes. |psy-taliro| uses the built-in :py:mod:`multiprocessing` module, which uses the
:py:mod:`pickle` module for data serialization. This means that only cost functions and optimizers
which can be serialized with ``pickle`` can be used in tests with multiple processes. Closures and
other data types which depend on local variables cannot be used in this context because they cannot
be serialized.

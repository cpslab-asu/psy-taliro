Quickstart
==========

Virtual environments
--------------------

Python packages are installed to a global location by default, so to avoid conflicts the python
community has adopted virtual environments which create locations to keep dependencies separate.
Many tools have been developed to help manage virtual environments, the following are a few of the
most common.

Virtualenv
^^^^^^^^^^

The oldest of the virtual environment management tools, the virtualenv command is fairly primitive
in comparison to the other tools described here. Virtual environments can be created by running the
command::

    virtualenv <directory name>

Traditionally, virtual environments are stored in a directory named ``venv``, sometimes written
``.venv`` to hide it from command line tools. A virtual env can be activated by running the
command::

    source <virtualenv directory>/bin/activate

This will open a shell configured to install packages to the local directory instead of the global
one. After activating the virtual environment, the normal pip and python commands can be used.

Pipenv
^^^^^^

`pipenv <https://pipenv.pypa.io>`_ is a tool designed to emulate packaging tools like
`npm <https://npmjs.com>`_from Javascript or `cargo <https://crates.io>`_ from Rust. The pipenv
tool creates a ``Pipfile.lock`` file which specifies the exact version of every dependency to
install. The purpose of this file to ensure that running the install command on any machine results
in the same exact environment. Pipenv manages the virtualenv folder for you in a special directory.
Pipenv can be installed using pip::

    pip install pipenv

Once installed, a pipenv-managed virtual environment can be created using the command::

    pipenv --three

Packages can be installed using the ``install`` command::

    pipenv install psy-taliro

Finally, command can be run inside the virtual environment by prefixing the command with ``pipenv run``::

    pipenv run python3 myscript.py

A virtual environment shell can be opened by using the command::

    pipenv shell

This has been a rapid overview of the pipenv tool. For more information please consult the pipenv
manual.

Poetry
^^^^^^

Like pipenv, poetry manages virtual environments using a lock file. Installation instructions for
poetry can be found on its `website <https://python-poetry.org>`_. Once installed, a poetry managed
virtual environment can be created by running the command::

    poetry init

Packages can be installed using the ``add`` command::

    poetry add psy-taliro

Finally, a command can be run inside a virtual environment by prefixing the command with
``poetry run``::

    poetry run python3 myscript.py

More information about the poetry tool can be found in the poetry manual.

Other tools
^^^^^^^^^^^

There are many other environment managers for python like Conda or flit which can also be used to
install python packages in isolation. Covering all of the tools is out of the scope of this
documentation, but the pipenv and poetry tools have been used extensively by PSY-TaLiRo.

Basic concepts
--------------

A PSY-TaLiRo test is defined using four components, which can be defined in any order.

Models
^^^^^^

A model is a representation of a system. PSY-TaLiRo provides two types of models:

- :ref:`Blackbox <blackbox>` model
- :ref:`ODE <ode>` model

There models can be constructed using decorators provided by PSY-TaLiRo like so:

.. code-block:: python

    from staliro import blackbox, ode
    
    @blackbox(sampling_interval=0.2)
    def blackbox_model(static_params, signal_times, signal_values):
        ...

    @ode()
    def ode_model(time, state, signal_values):
        ...

All models must return an array of states and a corresponding array of timestamps, both of which
represent the system state over time. 

Specifications
^^^^^^^^^^^^^^

A specification represents a requirement of the system being tested. PSY-TaLiRo provides three
different specifications implemented using two different libraries. The first library is 
`TLTK <https://bitbucket.org/versyslab/tltk/src/master/>`_ which is used to implement the
:ref:`TLTK <tltk>` specification. The second library is `RTAMT <https://github.com/nickovic/rtamt>`_
which is used to implement the :ref:`RTAMT Dense <rtamt_dense>` and
:ref:`RTAMT Discrete <rtamt_discrete>` optimizers.

Signal Temporal Logic
^^^^^^^^^^^^^^^^^^^^^

All specifications provided by PSY-TaLiRo express system requirements using Signal Temporal Logic,
or STL. STL is a higher-order logic which provides operators that can quantify boolean expressions,
referred to as **predicates**, over a time interval. 

STL predicates are written in the following form::

    name (<=|>=) (1|1.0|1e0)

STL formulas written for PSY-TaLiRo can include the following operators:

+-------------------------+------------------------------+
| Operator name           | Representation               |
+=========================+==============================+
| And                     | ``and``, ``&&``, or ``/\``   |
+-------------------------+------------------------------+
| Or                      | ``or``, ``||``, or ``\/``    |
+-------------------------+------------------------------+
| Not                     | ``not`` or ``!``             |
+-------------------------+------------------------------+
| Implication             | ``implies`` or ``->``        |
+-------------------------+------------------------------+
| Biconditional           | ``<->``                      |
+-------------------------+------------------------------+
| Next [#discrete]_       | ``next`` or ``X``            |
+-------------------------+------------------------------+
| Eventually [#interval]_ | ``eventually``, ``F``        |
+-------------------------+------------------------------+
| Always [#interval]_     | ``always`` or ``G``          |
+-------------------------+------------------------------+
| Until [#interval]_      | ``until`` or ``U``           |
+-------------------------+------------------------------+

.. rubric:: Notes

.. [#discrete] Only supported for discrete time specifications
.. [#interval] Operator optionally supports an interval written ``OP[t_starts, t_end] ...``. Without
               an interval, an operator applies for all time.

Some example requirements are written below:

+-------------------------------------------+--------------------------------------------------------------------------------------------------------+
| Requirement                               | STL representation                                                                                     |
+===========================================+========================================================================================================+
| Do not come in contact with the ground    | ``always (altitude >= 0)``                                                                             |
+-------------------------------------------+--------------------------------------------------------------------------------------------------------+
| Never enter the zone                      | ``G (not (x <= 10 and x >= 20 and y <= 5 and y >= 0))``                                                |
+-------------------------------------------+--------------------------------------------------------------------------------------------------------+
| Exit the zone 4 seconds after entering it | ``(x <= 10 and x >= 20 and y <= 5 and y >= 0) -> F[0,4] !(x <= 10 and x >= 20 and y <= 5 and y >= 0)`` |
+-------------------------------------------+--------------------------------------------------------------------------------------------------------+

Optimizers
^^^^^^^^^^

An optimizer is responsible for selecting samples that the model

Writing tests
-------------

Executing tests
---------------

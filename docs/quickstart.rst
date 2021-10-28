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
command

.. code-block:: console

    virtualenv <directory name>

Traditionally, virtual environments are stored in a directory named ``venv``, sometimes written
``.venv`` to hide it from command line tools. A virtual env can be activated by running the
command

.. code-block:: console

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
Pipenv can be installed using pip

.. code-block:: console

    pip install pipenv

Once installed, a pipenv-managed virtual environment can be created using the command

.. code-block:: console

    pipenv --three

Packages can be installed using the ``install`` command

.. code-block:: console

    pipenv install psy-taliro

Finally, command can be run inside the virtual environment by prefixing the command with ``pipenv run``

.. code-block:: console

    pipenv run python3 myscript.py

A virtual environment shell can be opened by using the command

.. code-block:: console

    pipenv shell

This has been a rapid overview of the pipenv tool. For more information please consult the pipenv
manual.

Poetry
^^^^^^

Like pipenv, poetry manages virtual environments using a lock file. Installation instructions for
poetry can be found on its `website <https://python-poetry.org>`_. Once installed, a poetry managed
virtual environment can be created by running the command

.. code-block:: console

    poetry init

Packages can be installed using the ``add`` command

.. code-block:: console

    poetry add psy-taliro

Finally, a command can be run inside a virtual environment by prefixing the command with
``poetry run``

.. code-block:: console

    poetry run python3 myscript.py

More information about the poetry tool can be found in the poetry manual.

Other tools
^^^^^^^^^^^

There are many other environment managers for python like Conda or flit which can also be used to
install python packages in isolation. Covering all of the tools is out of the scope of this
documentation, but the pipenv and poetry tools have been used extensively by PSY-TaLiRo.

Components
----------

A PSY-TaLiRo test is defined using four components, which can be defined in any order. These
components are the:

- model
- specification
- optimizer
- options

Very simply, the optimizer is called with the model, specification and options objects.  Using the
sample space defined in the options object, the optimizer selects samples and passes them to the
model. The model separates the sample into time invariant and time-varying system inputs according
to the values defined in the options object. The time-varying inputs are used to create
interpolator functions which represent the signal over the simulation interval. The separated
system inputs are used to set up and execute the system simulation and the model returns an array of
states and an array of time values. The model outputs are passed to the specification which uses
them to generate a single scalar value. The specification output is returned to the optimizer,
where it can be used to inform the selection of another sample.

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

All models expose a method named ``simulate`` which must accept the static and time-varying system
inputs and return an array of states and a corresponding array of timestamps which together
represent the system state over time. 

Specifications
^^^^^^^^^^^^^^

A specification represents a requirement of the system being tested. PSY-TaLiRo provides three
different specifications implemented using two different backends. The first library is 
`TLTK <https://bitbucket.org/versyslab/tltk/src/master/>`_ which is used to implement the
:ref:`TLTK <tltk>` specification. The second library is `RTAMT <https://github.com/nickovic/rtamt>`_
which is used to implement the :ref:`RTAMT Dense <rtamt_dense>` and
:ref:`RTAMT Discrete <rtamt_discrete>` optimizers. PSY-TaLiRo specifications are constructed using
by providing a requirement and a dictionary that is used to map state columns to the requirement
like so:

.. code-block:: python

    from staliro import TLTK, RTAMTDense, RTAMTDiscrete, PredicateProps

    requirement = "[](altitude >= 0)"
    pred_dict = {"altitude": PredicateProps(0, "float")}

    tltk = TLTK(requirement, pred_dict)
    rtamt_dense = RTAMTDense(requirement, pred_dict)
    rtamt_discrete = RTAMTDiscrete(requirement, pred_dict)

All specifications expose a method named ``evaluate`` which must accept the array of states and the
array of times from the model and return a single scalar value that represents the "goodness" of
the system output with respect to the trajectory. 

Signal Temporal Logic
^^^^^^^^^^^^^^^^^^^^^

All specifications provided by PSY-TaLiRo express system requirements using Signal Temporal Logic,
or STL. STL is a higher-order logic which provides operators that can quantify boolean expressions,
referred to as **predicates**, over a time interval. 

STL predicates are written in the following form

.. code-block::

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

An optimizer is responsible for selecting samples that the model will use to execute a simulation.
At its core an optimizer provides samples to a **cost function** which returns a single scalar
value. The goal of the optimizer is to find the lowest cost value.  Different optimizers can have
different strategies for selecting samples. Some optimizers will use the result of the last
simulation to help guide the selection of the next sample, while some optimizers may not.
Optimizers also have the option of vectorizing sample evaluation to call the cost function in
parallel.

The cost function for PSY-TaLiRo is a composition of the model and the specification. After the
model executes a simulation, the output is passed to the specification for analysis. The result
is a single value which is returned to the optimizer. 

An optimizer exposes the ``optimize`` method which must accept the cost function and a
parameter object that controls the optimization behavior, and return an arbitrary value.

PSY-TaLiRo provides two optimizers: :ref:`Uniform Random <uniform_random>` and
:ref:`Simulated Annealing <simulated_annealing>`. These optimizers can be easily constructed by
calling them with no arguments like so:

.. code-block:: python

    from staliro import UniformRandom, DualAnnealing

    ur_optimizer = UniformRandom()
    da_optimizer = DualAnnealing()

Options
^^^^^^^

The options object is provided to configure the behavior of the other components. After the
``staliro`` function has finished running, the options object is attached to the result so that
it can be included in analysis. The options object requires that either the ``static_parameters``
or ``signals`` properties be filled, but all other properties are optional. Some common options are

+-------------------+----------------------------------------------------------------------------------------+
| Option            | Description                                                                            |
+===================+========================================================================================+
| static_parameters | Time-invariant model inputs. Often used to represent initial conditions of the system. |
+-------------------+----------------------------------------------------------------------------------------+
| signals           | Time-varying model inputs                                                              |
+-------------------+----------------------------------------------------------------------------------------+
| runs              | Number of times to execute the optimizer                                               |
+-------------------+----------------------------------------------------------------------------------------+
| iterations        | Number of samples to evaluate per run                                                  |
+-------------------+----------------------------------------------------------------------------------------+
| seed              | Initial seed of the random number generator. Necessary for repeatability               |
+-------------------+----------------------------------------------------------------------------------------+

The options object is constructed like so:

.. code-block:: python

    from staliro import Options

    options = Options(static_parameters=[(0, 10), (100, 101)], runs=10, iterations=1000)

Writing tests
-------------

A typical PSY-TaLiRo script is composed of component definitions and then a call to the ``staliro``
function. The ``staliro`` takes as input a model instance, a specification instance, an optimizer
instance, and an options instance. As output, the ``staliro`` function returns a
:ref:`Result <result>` object which contains the result data from each run of the optimizer, as
well as an evaluation history from the cost function.

Executable scripts 
^^^^^^^^^^^^^^^^^^

Keeping tests in executable scripts can be convienent if you plan on executing a test many times.
Python has a few idioms for creating executable scripts which can make them much easier to work
with. The first is a comment line called a
`shebang <https://en.wikipedia.org/wiki/Shebang_(Unix)>`_.

.. code-block:: python

    #!/usr/bin/env python3

This instructs the system on how to select the python interpreter to use when executing the script.
The second important idiom is the main guard.

.. code-block:: python

    if __name__ == "__main__":
        ...

The purpose of the main guard is to avoid executing code unless the module is itself
being executed as the top-level script. For more information about the main guard, you can
consult the Python `documentation <https://docs.python.org/3/library/__main__.html>`_.

Putting these together, we get a module that looks like the following:

.. code-block:: python

    #!/usr/bin/env python3

    # Define test components
    model = ...
    specification = ...
    optimizer = ...
    options = ...

    if __name__ == "__main__":
        result = staliro(model, specification, optimizers, options)
        # Process result

Analyzing test results
----------------------

The output of the ``staliro`` function is a result object, which has two attributes:

- ``runs``
- ``options``

The ``runs`` attribute has the result of each run of the optimizer. Each result contains the output
of the optimizer, as well as the evaluation history of the cost function for that run. The result
from the optimizer is accessible as the ``result`` attribute, the history is available as the
``history`` attribute, and the total runtime as the ``duration`` attribute. The result object also
has the properties ``best_iter`` and ``fastest_iter`` that correspond to evaluations in the history.
Each element of the history is an :ref:`Evaluation <evaluation>` instance which contains the
``sample``, ``cost``, ``extra`` and ``timing`` information from the evaluation.

The ``options`` attribute of the result object contains the options object that was provided to the
``staliro`` function to be used as reference or for storage.

One method of processing the result of the ``staliro`` function could be as follows:

.. code-block:: python

    result = staliro(model, specification, optimizer, options)

    for run in result.runs:
        print(run.duration)
        print(run.best_iter)
        print(run.fastest_iter)

        for evaluation in run.history:
            print(evaluation.sample)
            print(evaluation.cost)
            print(evaluation.extra)

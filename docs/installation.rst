.. include:: _substitutions.rst

============
Installation
============

In order to use |psy-taliro|, you will need to install the package into your Python environment.
Installation of Python packages is handled by the ``pip`` program. You can install this project
using ``pip`` like so:

.. code-block:: shell

    pip install psy-taliro

``pip`` will attempt to install packages to the system-wide Python location by default. If you
you do not have permission to install packages to this location, you can install |psy-taliro|
to a user-specific Python location using the ``--user`` flag like so:

.. code-block:: shell

    pip install --user psy-taliro

Since Python packages are all installed to a single location, conflicts can arise if multiple
packages depend on the same package but use different versions since only the last-installed version
will be kept. To avoid conflicts the Python community has adopted *virtual environments* which create
project-specific python environments to keep dependencies separate. Many tools have been developed
to help manage virtual environments, the following sections covers the installation for a few of the
most common.

Virtualenv
----------

The oldest of the virtual environment management tools, the ``virtualenv`` package provides very low
-level in comparison to the other tools described here. To install ``virtualenv``, run the following
command in your terminal:

.. code-block:: shell

   python3 -m pip install --user virtualenv

Once installed, ``virtualenv`` can be used to create virtual environments with the command:

.. code-block:: shell

    virtualenv <directory name>

Traditionally, virtual environments are stored in a directory named ``venv``, sometimes written
``.venv`` to hide it from command line tools. Once created, a virtual environment can be activated
by running the command

.. code-block:: shell

    source <virtualenv directory>/bin/activate

This will open a shell configured to install packages to the virtual environment instead of
globally. After activating the virtual environment, the normal ``pip`` and ``python3`` commands
can be used.

Starting in Python 3.3, a limited version of the ``virtualenv`` library is pre-installed called
``venv``. The advantage of this built-in library is that for simple tasks you do not need to install
an additional package, but for more advanced workflows installing ``virtualenv`` is still necessary.
To create a virtual environment using the built-in ``venv`` library you can use the following
command:

.. code-block:: shell

   python3 -m venv <directory name>

Once you have created and activated the virtual environment, |psy-taliro| can be installed using
the typical ``pip`` command.

.. code-block:: shell

   <virtualenv directory>/bin/pip install psy-taliro

Pipenv
------

`Pipenv <https://pipenv.pypa.io>`_ is a tool designed to emulate packaging tools like
`npm <https://npmjs.com>`_ from Javascript or `cargo <https://crates.io>`_ from Rust. The ``pipenv``
tool creates a ``Pipfile.lock`` file which specifies the exact version of every dependency to
install, the purpose of which is to ensure reproducible environments when deploying a package.
``pipenv`` stores every virtual environment for you in a special directory to avoid conflicts. While
``pipenv`` can be installed using the ``pip`` command, it is recommended to install the package
using `pipx <https://pipx.pypa.io>`_ instead. Once you install ``pipx`` on your system, you can
install ``pipenv`` with the following command.

.. code-block:: shell

    pipx install pipenv

Once installed, a ``pipenv``-managed virtual environment can be created using the command

.. code-block:: shell

    pipenv --three

|psy-taliro| can be installed to the virtual environment without activating it using the ``install``
sub-command.

.. code-block:: shell

    pipenv install psy-taliro

Finally, python scripts can be executed within the virtual environment by prefixing the normal run
command with ``pipenv run``.

.. code-block:: shell

    pipenv run python3 <script name>

If needed, a pipenv-managed virtual environment can be activated by using the command

.. code-block:: shell

    pipenv shell

Poetry
------

Like :ref:`pipenv`, poetry is another tool to create and manage virtual environments. Installation
instructions for poetry can be found on its `website <https://python-poetry.org>`_. Once installed,
a poetry-managed virtual environment can be created by running the command

.. code-block:: shell

    poetry init

You can install |psy-taliro| using the ``add`` sub-command.

.. code-block:: shell

    poetry add psy-taliro

Finally, a script can be run inside a virtual environment by prefixing the command with
``poetry run``

.. code-block:: shell

    poetry run python3 <script name>

Conda
-----

Other tools
-----------

There are many other environment managers for python like `conda <https://docs.conda.io>`_ , 
`hatch <https://hatch.pypa.io>`_, or `pdm <https://pdm.pypa.io>`_ which can also be used to
install python packages in isolation. Covering all of the tools is out of the scope of this
documentation, but the pipenv and poetry tools are mentioned here because they have been used
frequently in our work.

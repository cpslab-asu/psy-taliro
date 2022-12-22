# $\Psi$-TaLiRo

An extensible Python toolbox for search-based test generation for cyber-physical
systems. This work is based of the MATLAB toolbox S-TaLiRo, which is available
[here](https://sites.google.com/a/asu.edu/s-taliro/s-taliro).

## Models

$\Psi$-TaLiRo represents the cyber-physical system under test as a model.
Conceptually, a model is a function that maps a set of system inputs to a
timed series of states called a _Trace_. $\Psi$-TaLiRo provides two ways to
construct a model: the __Blackbox__ and __Ode__ models. The __Blackbox__ model
makes no assumptions about the underlying system it represents. The __Ode__
model expects the underlying model to be represented using ordinary
differential equations.

## Specifications

$\Psi$-TaLiRo tests are system requirements expressed in metric temporal logic
(MTL). Evaluation of the system requirement depends on a _monitor_, and
$\Psi$-TaLiRo supports several options. All specific implementations are
available in the `staliro.specifications` module. To use a specification, you
will need to ensure that the monitor library is installed. Additional
information is available in the table below:

| Monitor            | Installation           | Link                                             |
| ------------------ | ---------------------- | ------------------------------------------------ |
| RTAMT              | `pip install rtamt`    | [homepage](https://github.com/nickovic/rtamt)    |
| TLTK (*Linux only) | `pip install tltk_mtl` | [homepage](https://bitbucket.org/versyslab/tltk) |
| Py-TaLiRo          | `pip install pytaliro` | [homepage](https://gitlab.com/sbtg/py-taliro)    |

## Optimizers

$\Psi$-TaLiRo generates inputs for the system under test by using an optimizer.
The optimizers provided by the toolbox are the __UniformRandom__ and
__DualAnnealing__ optimizers in the `staliro.optimizers` module.

For other optimizer options, see the [PartX](https://gitlab.com/bose1/part-x)
repository. There you will find additional implementations that give extra
guarantees about the system input space.

## Type hints

This toolbox provides [PEP484](https://peps.python.org/pep-0484) type hints
to help ensure correct usage. To use the type hints, you will need to install
one of the several type hint checkers available for python. A non-exhaustive
list is:

- [MyPy](https://mypy.readthedocs.io)
- [Pyright](https://github.com/microsoft/pyright)
- [Pyre](https://github.com/facebook/pyre-check)
- [Pytype](https://github.com/google/pytype)

The easiest way to get started is to install
[VSCode](https://code.visualstudio.com) with the
[python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
which includes the _pyright_ type checker.

## Installation

To install this toolbox, run the command `pip install psy_taliro`. To avoid
installing python packages globally, you can use a virtual environment to
keep the packages in a project-specific directory. Some of the tools for
managing virtual environments are:

- [Pipenv](https://pipenv.pypa.io)
- [Poetry](https://python-poetry.org)
- [Venv](https://docs.python.org/3/library/venv.html)

(Anaconda)[https://www.anaconda.com] can also be used to create separate python
environments, and may be easier to set up on some systems.

## Example

```python
from math import pi

from staliro import models, optimizers, specifications
from staliro.options import Options
from staliro.staliro import staliro


@models.blackbox()
def aircraft_model(X, T, U):
    """Blackbox model that represents the dynamics of an aircraft.

    Arguments:
        X: The static (initial) inputs to the system. A four-element vector of
           the form [roll, pitch, yaw, thrust].
        T: Interpolation times for the input signals
        U: Interpolated values of the time-varying input signals

    Returns:
        trace: A set of timed state values representing the altitude of the
               aircraft over time
    """
    ...


optimizer = optimizers.UniformRandom()
requirement = "[] (alt > 0.0)"  # Requirement that the aircraft does not crash
specification = specifications.RTAMTDense(requirements, {"alt": 0})  # The altitude value is in the first column of the aircraft trace states
options = Options(
    runs=10,  # 10 independent optimization attempts
    iterations=100,  # Generate 100 samples per optimization attempt
    interval=(0.0, 2.0),  # Simulation interval is from 0 to 2 seconds
    static_parameters=[
        (-pi / 4, pi / 4),  # Roll
        (-pi / 4, pi / 4),  # Pitch
        (-pi / 4, pi / 4),  # Yaw
        (0, 100),           # Thrust
    ]
)

result = staliro(aircraft_model, specification, optimizer, options)
```

## Documentation

For additional details about the toolbox components, or example scripts, refer
to the [documentation site](https://sbtg.gitlab.io/psy-taliro).

## Citing this project

If you use this toolbox in your research, include this citation in your
bibliography

```bibtex
@misc{psy-taliro,
  doi = {10.48550/ARXIV.2106.02200},
  url = {https://arxiv.org/abs/2106.02200},
  author = {Thibeault, Quinn and Anderson, Jacob and Chandratre, Aniruddh and Pedrielli, Giulia and Fainekos, Georgios},
  keywords = {Software Engineering (cs.SE), Systems and Control (eess.SY), FOS: Computer and information sciences, FOS: Computer and information sciences, FOS: Electrical engineering, electronic engineering, information engineering, FOS: Electrical engineering, electronic engineering, information engineering},
  title = {PSY-TaLiRo: A Python Toolbox for Search-Based Test Generation for Cyber-Physical Systems},
  publisher = {arXiv},
  year = {2021},
  copyright = {arXiv.org perpetual, non-exclusive license}
}
```


from math import cos, pi, sin

from numpy import array, float64, ndarray
from staliro import staliro
from staliro.models import ode
from staliro.optimizers import DualAnnealing
from staliro.options import SignalOptions, StaliroOptions
from staliro.signals import LinearFactory
from staliro.specification import Specification
from tltk_mtl import Predicate


@ode()
def aircraft_ode(time: float, states: ndarray, signals: ndarray) -> ndarray:
    b = (0.07351, -1.5e-3, 6.1e-4)
    c = (0.1667, 0.109)
    m = 74e3
    g = 9.81
    s = 158
    rho = 0.3804

    mat1 = array(
        [
            (-s * rho * b[0] * states[0] ** 2) / (2 * m) - g * sin(pi * states[1] / 180),
            (s * rho * c[0] * states[0]) / (2 * m) - g * cos(pi * states[1] / 180) / states[0],
            states[0] * sin(pi * states[1] / 180),
        ]
    )

    mat2 = array([signals[0] / m, 0.0, 0.0])

    mat3 = array(
        [
            (-s * rho * states[0] ** 2) / (2 * m) * (b[1] * signals[1] + b[2] * signals[1] ** 2),
            (s * rho * c[1]) / (2 * m) * states[0] * signals[1],
            0,
        ]
    )

    return mat1 + mat2 + mat3  # type: ignore


initial_conditions = [(200.0, 260.0), (-10.0, 10.0), (120.0, 150.0)]
signals = [
    SignalOptions(interval=(34386.0, 53973.0)),
    SignalOptions(interval=(0.0, 16.0), control_points=20, factory=LinearFactory()),
]

phi = "!([]_[0,4.0]a /\ <>_[3.5,4.0]b)"

A = array([[1, 0, 0], [-1, 0, 0]], dtype=float64)
predicates = {
    "a": Predicate("a", A, array([250, -240], dtype=float64)),
    "b": Predicate("b", A, array([240.1, -240], dtype=float64)),
}

spec = Specification(phi, predicates)

options = StaliroOptions(
    runs=1, iterations=10, static_parameters=initial_conditions, signals=signals
)

# Example using the first falsify method where optimizer is passed by value
results = staliro(phi, predicates, aircraft_ode, options, DualAnnealing())

for i, result in enumerate(results.runs):
    print(f"Run {i} lowest robustness found: {result.best_iter.robustness}")

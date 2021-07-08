from math import cos, pi, sin

from numpy import array
from staliro import staliro
from staliro.models import ode, State, SignalValues
from staliro.optimizers import UniformRandom
from staliro.options import SignalOptions, Options
from staliro.signals import LinearFactory
from staliro.specification import PredicateProps, TLTK


@ode()
def aircraft_ode(time: float, state: State, signals: SignalValues) -> State:
    b = (0.07351, -1.5e-3, 6.1e-4)
    c = (0.1667, 0.109)
    m = 74e3
    g = 9.81
    s = 158
    rho = 0.3804

    mat1 = array(
        [
            (-s * rho * b[0] * state[0] ** 2) / (2 * m) - g * sin(pi * state[1] / 180),
            (s * rho * c[0] * state[0]) / (2 * m) - g * cos(pi * state[1] / 180) / state[0],
            state[0] * sin(pi * state[1] / 180),
        ]
    )

    mat2 = array([signals[0] / m, 0.0, 0.0])

    mat3 = array(
        [
            (-s * rho * state[0] ** 2) / (2 * m) * (b[1] * signals[1] + b[2] * signals[1] ** 2),
            (s * rho * c[1]) / (2 * m) * state[0] * signals[1],
            0,
        ]
    )

    return mat1 + mat2 + mat3  # type: ignore


initial_conditions = [(200.0, 260.0), (-10.0, 10.0), (120.0, 150.0)]
signals = [
    SignalOptions(interval=(34386.0, 53973.0)),
    SignalOptions(interval=(0.0, 16.0), control_points=20, factory=LinearFactory()),
]

phi = "!([](0,4.0)(a <= 250 /\ a >= 240) /\ <>(3.5,4.0)(b <= 240.1 /\ b >= 240)"
predicates = {
    "a": PredicateProps(0, "float"),
    "b": PredicateProps(0, "float"),
}

spec = TLTK(phi, predicates)

options = Options(runs=1, iterations=10, static_parameters=initial_conditions, signals=signals)

optimizer = UniformRandom()

# Example using the first falsify method where optimizer is passed by value
result = staliro(aircraft_ode, spec, optimizer, options)

for n, run in enumerate(result.runs):
    print(f"Run {n} - Best iteration: {run.best_iter}")

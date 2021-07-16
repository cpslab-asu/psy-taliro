import math
import statistics

import numpy as np
import staliro
import staliro.signals as signals
import staliro.models as models


@models.ode()
def aircraft_model(time: float, state: models.State, signals: models.SignalValues) -> models.State:
    b = (0.07351, -1.5e-3, 6.1e-4)
    c = (0.1667, 0.109)
    m = 74e3
    g = 9.81
    s = 158
    rho = 0.3804

    mat1 = np.array(
        [
            (-s * rho * b[0] * state[0] ** 2) / (2 * m) - g * math.sin(math.pi * state[1] / 180),
            (s * rho * c[0] * state[0]) / (2 * m)
            - g * math.cos(math.pi * state[1] / 180) / state[0],
            state[0] * math.sin(math.pi * state[1] / 180),
        ]
    )

    mat2 = np.array([signals[0] / m, 0.0, 0.0])

    mat3 = np.array(
        [
            (-s * rho * state[0] ** 2) / (2 * m) * (b[1] * signals[1] + b[2] * signals[1] ** 2),
            (s * rho * c[1]) / (2 * m) * state[0] * signals[1],
            0,
        ]
    )

    return mat1 + mat2 + mat3  # type: ignore


phi = "!([](0,4.0)(a <= 250 /\ a >= 240) /\ <>(3.5,4.0)(b <= 240.1 /\ b >= 240)"
predicates = {
    "a": staliro.PredicateProps(0, "float"),
    "b": staliro.PredicateProps(0, "float"),
}
spec = staliro.RTAMTDense(phi, predicates)

initial_conditions = [(200.0, 260.0), (-10.0, 10.0), (120.0, 150.0)]
signal_options = [
    staliro.SignalOptions(interval=(34386.0, 53973.0)),
    staliro.SignalOptions(interval=(0.0, 16.0), control_points=20, factory=signals.LinearFactory()),
]
options = staliro.Options(
    static_parameters=initial_conditions,
    signals=signal_options,
    runs=1,
    iterations=100,
    interval=(0, 4),
)

optimizer = staliro.UniformRandom()

result = staliro.staliro_timed(aircraft_model, spec, optimizer, options)

for run in result.runs:
    avg_model_duration = statistics.mean(iteration.model_duration for iteration in run.history)
    total_model_time = sum(iteration.model_duration for iteration in run.history)

    avg_cost_duration = statistics.mean(iteration.cost_duration for iteration in run.history)
    total_cost_time = sum(iteration.cost_duration for iteration in run.history)

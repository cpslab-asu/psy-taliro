from math import cos, pi
from typing import Any, Sequence

import plotly.graph_objects as go
from staliro.models import ode
from staliro.options import Options
from staliro.optimizers import UniformRandom
from staliro.specifications import RTAMTDense
from staliro.staliro import staliro, simulate_model


@ode()
def nonlinear_model(time: float, state: Sequence[float], signals: Any) -> Sequence[float]:
    return [state[0] - state[1] + 0.1 * time, state[1] * cos(2 * pi * state[0]) + 0.1 * time]


initial_conditions = [(-1, 1), (-1, 1)]
phi = r"[]!(a >= -1.6 /\ a <= -1.4  /\ b >= -1.1 /\ b <= -0.9)"
specification = RTAMTDense(phi, {"a": 0, "b": 1})
options = Options(runs=1, iterations=1000, static_parameters=initial_conditions)
optimizer = UniformRandom()

result = staliro(nonlinear_model, specification, optimizer, options)

best_run = result.best_run
best_sample = best_run.best_eval.sample
best_result = simulate_model(nonlinear_model, options, best_sample)

figure = go.Figure()
figure.add_trace(go.Scatter(x=[-1.6, -1.4], y=[-1.1, -0.9], fill="toself", color="red"))
figure.add_trace(go.Scatter(x=[-1, 1], y=[-1, 1], fill="toself", color="green"))
figure.add_trace(
    go.Scatter(
        x=[test.sample[0] for test in best_run.history],
        y=[test.sample[1] for test in best_run.history],
    ),
    marker_symbol="asterisk",
)
figure.add_trace(go.Scatter(x=best_result.states[0], y=best_result.states[1]))

import logging
import math
from collections.abc import Sequence

import numpy as np
import plotly.graph_objects as go
from aerobench.examples.gcas.gcas_autopilot import GcasAutopilot
from aerobench.run_f16_sim import run_f16_sim

from staliro.core import BasicResult, ModelResult, Trace, best_eval, best_run
from staliro.models import SignalTimes, SignalValues, blackbox
from staliro.optimizers import DualAnnealing
from staliro.options import Options
from staliro.specifications import RTAMTDense
from staliro.staliro import simulate_model, staliro

F16DataT = ModelResult[list[float], None]


@blackbox()
def f16_model(static: Sequence[float], times: SignalTimes, signals: SignalValues) -> F16DataT:
    power = 9
    alpha = np.deg2rad(2.1215)
    beta = 0
    alt = 2330
    vel = 540
    phi = static[0]
    theta = static[1]
    psi = static[2]

    initial_state = [vel, alpha, beta, phi, theta, psi, 0, 0, 0, 0, 0, 0, alt, power]
    step = 1 / 30
    autopilot = GcasAutopilot(init_mode="roll", stdout=False)

    result = run_f16_sim(initial_state, max(times), autopilot, step, extended_states=True)

    states = np.vstack(
        (
            np.array([0 if x == "standby" else 1 for x in result["modes"]]),
            result["states"][:, 4],  # roll
            result["states"][:, 5],  # pitch
            result["states"][:, 6],  # yaw
            result["states"][:, 12],  # altitude
        )
    )
    timestamps: list[float] = result["times"]
    trace = Trace(timestamps, states.tolist())

    return BasicResult(trace)


phi = "always (alt > 0)"
specification = RTAMTDense(phi, {"alt": 4})

optimizer = DualAnnealing()

initial_conditions = [
    math.pi / 4 + np.array([-math.pi / 20, math.pi / 30]),  # PHI
    -math.pi / 2 * 0.8 + np.array([0, math.pi / 20]),  # THETA
    -math.pi / 4 + np.array([-math.pi / 8, math.pi / 8]),  # PSI
]
options = Options(runs=1, iterations=10, interval=(0, 15), static_parameters=initial_conditions)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    result = staliro(f16_model, specification, optimizer, options)

    best_sample = best_eval(best_run(result)).sample
    best_result = simulate_model(f16_model, options, best_sample)

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=best_result.trace.times,
            y=best_result.trace.states[4],
            mode="lines",
            line_color="green",
            name="altitude",
        )
    )
    figure.update_layout(xaxis_title="time (s)", yaxis_title="alt (m)")
    figure.add_hline(y=0, line_color="red")
    figure.write_image("f16.jpeg")

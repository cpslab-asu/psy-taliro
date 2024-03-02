import logging
import math

import numpy as np
import plotly.graph_objects as go
from aerobench.examples.gcas.gcas_autopilot import GcasAutopilot
from aerobench.run_f16_sim import run_f16_sim

from staliro import Options, Trace, staliro
from staliro.models import Blackbox, blackbox
from staliro.optimizers import DualAnnealing
from staliro.specifications import RTAMTDense


@blackbox()
def f16_model(inputs: Blackbox.Inputs) -> Trace[list[float]]:
    power = 9
    alpha = np.deg2rad(2.1215)
    beta = 0
    alt = 2330
    vel = 540
    phi = inputs.static["phi"]
    theta = inputs.static["theta"]
    psi = inputs.static["psi"]

    initial_state = [vel, alpha, beta, phi, theta, psi, 0, 0, 0, 0, 0, 0, alt, power]
    step = 1 / 30
    autopilot = GcasAutopilot(init_mode="roll", stdout=False)

    result = run_f16_sim(initial_state, max(inputs.times), autopilot, step, extended_states=True)
    times: list[float] = result["times"]
    states = np.vstack(
        (
            np.array([0 if x == "standby" else 1 for x in result["modes"]]),
            result["states"][:, 4],  # roll
            result["states"][:, 5],  # pitch
            result["states"][:, 6],  # yaw
            result["states"][:, 12],  # altitude
        )
    )

    return Trace(times, states.tolist())


specification = RTAMTDense("always (alt > 0)", {"alt": 4})
optimizer = DualAnnealing()
options = Options(
    runs=1,
    iterations=10,
    interval=(0, 15),
    static_parameters={
        "phi": math.pi / 4 + np.array([-math.pi / 20, math.pi / 30]),
        "theta": -math.pi / 2 * 0.8 + np.array([0, math.pi / 20]),
        "psi": -math.pi / 4 + np.array([-math.pi / 8, math.pi / 8]),
    },
)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    runs = staliro(f16_model, specification, optimizer, options)
    run = runs[0]
    min_cost_eval = min(run.evaluations, key=lambda e: e.cost)
    min_cost_trace = min_cost_eval.extra.trace

    figure = go.Figure()
    figure.update_layout(xaxis_title="time (s)", yaxis_title="alt (m)")
    figure.add_hline(y=0, line_color="red")
    figure.add_trace(
        go.Scatter(
            x=min_cost_trace.times,
            y=[state[4] for state in min_cost_trace.states],
            mode="lines",
            line_color="green",
            name="altitude",
        )
    )

    figure.write_image("f16.jpeg")


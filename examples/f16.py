import logging
import math

import numpy as np
import plotly.graph_objects as go
from aerobench.examples.gcas.gcas_autopilot import GcasAutopilot
from aerobench.run_f16_sim import run_f16_sim
from numpy.typing import NDArray

from staliro.core.model import Failure
from staliro.models import ModelData, SignalTimes, SignalValues, StaticInput, blackbox
from staliro.optimizers import DualAnnealing
from staliro.options import Options
from staliro.specifications import RTAMTDense
from staliro.staliro import simulate_model, staliro

F16DataT = ModelData[NDArray[np.float_], None]


@blackbox()
def f16_model(static: StaticInput, times: SignalTimes, signals: SignalValues) -> F16DataT:
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

    trajectories: NDArray[np.float_] = np.asarray([
        [0 if x == "standby" else 1 for x in result["modes"]],  # GCAS: autopilot (ap)
        result["states"][:, 4].T,                               # roll
        result["states"][:, 5].T,                               # pitch
        result["states"][:, 6].T,                               # yaw
        result["states"][:, 12].T                               # altitude
    ])

    timestamps: NDArray[np.float_] = result["times"]
    return ModelData(trajectories, timestamps)


phi_01 = "always[0:15] (alt > 0)"
phi_02 = "always[0:15] (((ap >= 0.5) and (next (ap <= 0.5))) implies (next ((roll >= 0.02 and roll <= 0.04) and (pitch >= 0.20 and pitch <= 0.28))))"

specification = RTAMTDense(phi_01, {"ap": 0, "roll": 1, "pitch": 2, "yaw": 3, "alt": 4})

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

    best_sample = result.best_run.best_eval.sample
    best_result = simulate_model(f16_model, options, best_sample)

    assert not isinstance(best_result, Failure)

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=best_result.times,
            y=best_result.states[0],
            mode="lines",
            line_color="green",
            name="altitude",
        )
    )
    figure.update_layout(xaxis_title="time (s)", yaxis_title="alt (m)")
    figure.add_hline(y=0, line_color="red")
    figure.write_image("f16.jpeg")

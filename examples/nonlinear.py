import logging
import math

import plotly.graph_objects as go

import staliro
import staliro.models as models
import staliro.optimizers as optimizers
import staliro.specifications as specifications


@models.ode()
def nonlinear_model(inputs: models.Ode.Inputs) -> list[float]:
    x1 = inputs.state["x1"]
    x2 = inputs.state["x2"]

    return [
        x1 - x2 + 0.1 * inputs.time,                          # x1_dot
        x2 * math.cos(2 * math.pi * x1) + 0.1 * inputs.time,  # x2_dot
    ]


phi = r"always !(a >= -1.6 and a <= -1.4  and b >= -1.1 and b <= -0.9)"
specification = specifications.RTAMTDense(phi, {"a": 0, "b": 1})
optimizer = optimizers.UniformRandom()
options = staliro.TestOptions(
    runs=1,
    iterations=100,
    tspan=(0, 2),
    static_inputs={
        "x1": (-1, 1),
        "x2": (-1, 1),
    },
)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    runs = staliro.test(nonlinear_model, specification, optimizer, options)
    run = runs[0]
    min_eval = min(run.evaluations, key=lambda e: e.cost)

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            name="Falsification area",
            x=[-1.6, -1.4, -1.4, -1.6],
            y=[-1.1, -1.1, -0.9, -0.9],
            fill="toself",
            fillcolor="red",
            line_color="red",
            mode="lines+markers",
        )
    )

    figure.add_trace(
        go.Scatter(
            name="Initial condition region",
            x=[-1, 1, 1, -1],
            y=[-1, -1, 1, 1],
            fill="toself",
            fillcolor="green",
            line_color="green",
            mode="lines+markers",
        )
    )

    figure.add_trace(
        go.Scatter(
            name="Samples",
            x=[evaluation.sample.static["x1"] for evaluation in run.evaluations],
            y=[evaluation.sample.static["x2"] for evaluation in run.evaluations],
            mode="markers",
            marker=go.scatter.Marker(color="lightblue", symbol="circle"),
        )
    )

    figure.add_trace(
        go.Scatter(
            name="Best evaluation trajectory",
            x=[state[0] for state in min_eval.extra.trace.states],
            y=[state[1] for state in min_eval.extra.trace.states],
            mode="lines+markers",
            line=go.scatter.Line(color="blue", shape="spline"),
        )
    )

    figure.write_image("nonlinear.jpeg")

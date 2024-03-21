import logging
import pathlib

import matlab
import matlab.engine
import numpy as np
import plotly.graph_objects as go
import plotly.subplots as sp

from staliro import Sample, SignalInput, TestOptions, staliro
from staliro.models import Model, Result
from staliro.optimizers import DualAnnealing
from staliro.specifications import rtamt


class AutotransModel(Model[list[float], None]):
    MODEL_NAME = "Autotrans_shift"

    def __init__(self) -> None:
        script_path = pathlib.Path(__name__)

        self.sampling_step = 0.2
        self.engine = matlab.engine.start_matlab()
        self.engine.addpath(str(script_path.parent))

        model_opts = self.engine.simget(AutotransModel.MODEL_NAME)
        self.model_opts = self.engine.simset(model_opts, "SaveFormat", "Array")

    def simulate(self, sample: Sample) -> Result[list[float], None]:
        assert sample.signals.tspan is not None

        tstart, tend = sample.signals.tspan
        duration = tend - tstart
        sim_t = matlab.double([0, tend])
        n_times = duration // self.sampling_step
        signal_times = np.linspace(tstart, tend, num=int(n_times))
        signal_values = np.array(
            [[signal.at_time(t) for t in signal_times] for signal in sample.signals]
        )

        model_input = matlab.double(np.row_stack((signal_times, signal_values)).T.tolist())
        timestamps, _, data = self.engine.sim(
            self.MODEL_NAME, sim_t, self.model_opts, model_input, nargout=3
        )

        times: list[float] = np.array(timestamps).flatten().tolist()
        states: list[list[float]] = list(data)

        return Result(times=times, states=states, extra=None)


model = AutotransModel()

phi = "always[0,30] (rpm >= 3000) -> (always[0,4] speed >= 35)"
specification = rtamt.parse_discrete(phi, {"rpm": 0, "speed": 1})

optimizer = DualAnnealing()

options = TestOptions(
    runs=1,
    iterations=100,
    tspan=(0, 30),
    signals={
        "throttle": SignalInput(control_points=[(0, 100)] * 7),
        "brake": SignalInput(control_points=[(0, 350)] * 3),
    },
)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    runs = staliro(model, specification, optimizer, options)
    run = runs[0]
    min_eval = min(run.evaluations, key=lambda e: e.cost)

    times = list(min_eval.extra.trace.times)
    rpm = [state[0] for state in min_eval.extra.trace.states]
    speed = [state[1] for state in min_eval.extra.trace.states]

    figure = sp.make_subplots(rows=2, cols=1, shared_xaxes=True, x_title="Time (s)")
    figure.add_trace(go.Scatter(x=times, y=rpm), row=1, col=1)
    figure.add_trace(go.Scatter(x=times, y=speed), row=2, col=1)
    figure.update_yaxes(title_text="RPM", row=1, col=1)
    figure.update_yaxes(title_text="Speed", row=2, col=1)
    figure.write_image("autotrans.jpeg")

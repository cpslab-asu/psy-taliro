import logging
from collections.abc import Sequence

import numpy as np
import plotly.graph_objects as go
import plotly.subplots as sp

from staliro.core.interval import Interval
from staliro.core.model import BasicResult, Model, ModelInputs, ModelResult, Trace
from staliro.core.result import best_eval, best_run
from staliro.core.signal import Signal
from staliro.optimizers import DualAnnealing
from staliro.options import Options, SignalOptions
from staliro.specifications import RTAMTDiscrete
from staliro.staliro import simulate_model, staliro

try:
    import matlab
    import matlab.engine
except ImportError:
    _has_matlab = False
else:
    _has_matlab = True


StaticInput = Sequence[float]
Signals = Sequence[Signal]
AutotransResultT = ModelResult[list[float], None]


class AutotransModel(Model[list[float], None]):
    MODEL_NAME = "Autotrans_shift"

    def __init__(self) -> None:
        if not _has_matlab:
            raise RuntimeError(
                "Simulink support requires the MATLAB Engine for Python to be installed"
            )

        engine = matlab.engine.start_matlab()
        engine.addpath("examples")
        model_opts = engine.simget(self.MODEL_NAME)

        self.sampling_step = 0.2
        self.engine = engine
        self.model_opts = engine.simset(model_opts, "SaveFormat", "Array")

    def simulate(self, inputs: ModelInputs, interval: Interval) -> BasicResult[list[float]]:
        sim_t = matlab.double([0, interval.upper])
        n_times = interval.length // self.sampling_step
        signal_times = np.linspace(interval.lower, interval.upper, int(n_times))
        signal_values = np.array(
            [[signal.at_time(t) for t in signal_times] for signal in inputs.signals]
        )
        model_input = matlab.double(np.row_stack((signal_times, signal_values)).T.tolist())

        timestamps, _, data = self.engine.sim(
            self.MODEL_NAME, sim_t, self.model_opts, model_input, nargout=3
        )

        timestamps_list: list[float] = np.array(timestamps).flatten().tolist()
        data_list: list[list[float]] = list(data)
        trace = Trace(timestamps_list, data_list)

        return BasicResult(trace)


model = AutotransModel()

phi = "always[0,30] (rpm >= 3000) -> (always[0,4] speed >= 35)"
specification = RTAMTDiscrete(phi, {"rpm": 0, "speed": 1})

optimizer = DualAnnealing()

signals = [
    SignalOptions(control_points=[(0, 100)] * 7),
    SignalOptions(control_points=[(0, 350)] * 3),
]
options = Options(runs=1, iterations=100, interval=(0, 30), signals=signals)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    result = staliro(model, specification, optimizer, options)

    best_sample = best_eval(best_run(result)).sample
    best_result = simulate_model(model, options, best_sample)
    rpm = best_result.trace.states[0]
    speed = best_result.trace.states[1]

    figure = sp.make_subplots(rows=2, cols=1, shared_xaxes=True, x_title="Time (s)")
    figure.add_trace(go.Scatter(x=best_result.trace.times, y=rpm), row=1, col=1)
    figure.add_trace(go.Scatter(x=best_result.trace.times, y=speed), row=2, col=1)
    figure.update_yaxes(title_text="RPM", row=1, col=1)
    figure.update_yaxes(title_text="Speed", row=2, col=1)
    figure.write_image("autotrans.jpeg")

import logging

import numpy as np
import plotly.graph_objects as go
import plotly.subplots as sp
from numpy.typing import NDArray
from staliro.core.interval import Interval
from staliro.core.model import Model, ModelData, Failure, StaticInput, Signals
from staliro.optimizers import DualAnnealing
from staliro.options import Options, SignalOptions
from staliro.specifications import TLTK
from staliro.staliro import staliro, simulate_model

try:
    import matlab
    import matlab.engine
except ImportError:
    _has_matlab = False
else:
    _has_matlab = True


AutotransDataT = NDArray[np.float_]
AutotransResultT = ModelData[AutotransDataT, None]


class AutotransModel(Model[AutotransDataT, None]):
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

    def simulate(self, static: StaticInput, signals: Signals, intrvl: Interval) -> AutotransResultT:
        sim_t = matlab.double([0, intrvl.upper])
        n_times = intrvl.length // self.sampling_step
        signal_times = np.linspace(intrvl.lower, intrvl.upper, int(n_times))
        signal_values = np.array([[signal.at_time(t) for t in signal_times] for signal in signals])
        model_input = matlab.double(np.row_stack((signal_times, signal_values)).T.tolist())

        timestamps, _, data = self.engine.sim(
            self.MODEL_NAME, sim_t, self.model_opts, model_input, nargout=3
        )

        timestamps_array = np.array(timestamps).flatten()
        data_array = np.array(data)

        return ModelData(data_array, timestamps_array)


model = AutotransModel()

phi = "always[0,30] (rpm >= 3000) -> (always[0,4] speed >= 35)"
specification = TLTK(phi, {"rpm": 0, "speed": 1})

optimizer = DualAnnealing()

signals = [
    SignalOptions((0, 100), control_points=7),
    SignalOptions((0, 350), control_points=3),
]
options = Options(runs=1, iterations=100, interval=(0, 30), signals=signals)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    result = staliro(model, specification, optimizer, options)

    best_sample = result.best_run.best_eval.sample
    best_result = simulate_model(model, options, best_sample)

    assert not isinstance(best_result, Failure)

    figure = sp.make_subplots(rows=2, cols=1, shared_xaxes=True, x_title="Time (s)")
    figure.add_trace(go.Scatter(x=best_result.times, y=best_result.states[0]), row=1, col=1)
    figure.add_trace(go.Scatter(x=best_result.times, y=best_result.states[1]), row=2, col=1)
    figure.update_yaxes(title_text="RPM", row=1, col=1)
    figure.update_yaxes(title_text="Speed", row=1, col=1)
    figure.write_image("autotrans.jpeg")

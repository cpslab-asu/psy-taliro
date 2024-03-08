from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from staliro import Trace
from staliro.specifications import RTAMTDense, RTAMTDiscrete

SIG_FIGS = 3
PHI = "(not ((always[0.0, 4.0]((x1 <= 250.0) and (x1 >= 240.0))) and (eventually[3.5,4.0]((x1 <= 240.1) and (x1 >= 240.0)))))"
EXPECTED = -0.0160623609618824


@pytest.fixture
def trace() -> Trace[list[float]]:
    test_path = Path(__file__)
    data_path = test_path.parent / "data" / "trajectory.csv"
    csv_data = pd.read_csv(str(data_path))
    timestamps = csv_data["t"].to_numpy(dtype=float)
    trajectories = csv_data["x1"].to_numpy(dtype=float)

    return Trace(times=timestamps.tolist(), states=np.atleast_2d(trajectories).T.tolist())


def test_rtamt_discrete(trace: Trace[list[float]]) -> None:
    print(list(trace.states))

    pytest.approx(RTAMTDiscrete(PHI, {"x1": 0}).evaluate(trace), EXPECTED, SIG_FIGS)


def test_rtamt_dense(trace: Trace[list[float]]) -> None:
    pytest.approx(RTAMTDense(PHI, {"x1": 0}).evaluate(trace), EXPECTED, SIG_FIGS)

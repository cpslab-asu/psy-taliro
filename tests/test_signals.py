from __future__ import annotations

from pathlib import Path
from unittest import TestCase

import numpy as np
import pandas as pd

from staliro.signals import pchip, piecewise_constant


def _random(lower: float, upper: float, size: int) -> list[float]:
    rng = np.random.default_rng()
    samples = rng.random(size)

    return [(upper - lower) * sample + lower for sample in samples]


class SignalTestCase(TestCase):
    TEST_DIR = Path(__file__).parent


class ConstantSignalTestCase(SignalTestCase):
    def test_constant_interpolator(self) -> None:
        interval = (0, 100)
        y_axis = [0, 1, 0, 1, 0, 0]
        x_axis = np.linspace(interval[0], interval[1], num=len(y_axis)).tolist()

        signal = piecewise_constant(x_axis, y_axis)
        csv_path = self.TEST_DIR / "data" / "constant_trace.csv"
        csv_data = pd.read_csv(str(csv_path))
        times_col = csv_data.columns[0]
        times = csv_data[times_col].tolist()
        sampled_values = np.array(signal.at_times(times))
        signal_col = csv_data.columns[1]

        np.testing.assert_equal(csv_data[signal_col].to_numpy(), sampled_values)

    def test_single_vs_vectorized(self) -> None:
        interval = (0, 100)
        y_axis = [0, 1, 0, 1, 0, 0]
        x_axis = np.linspace(interval[0], interval[1], num=len(y_axis)).tolist()
        times = _random(interval[0], interval[1], len(y_axis))

        signal = piecewise_constant(x_axis, y_axis)
        single_sampled_points = [signal.at_time(t) for t in times]
        vector_sampled_points = signal.at_times(times)

        self.assertListEqual(single_sampled_points, vector_sampled_points)


class PchipSignalTestCase(SignalTestCase):
    def test_pchip_interpolator(self) -> None:
        interval = (0, 4)
        y_axis = [
            36045.4877642653,
            41417.4995645605,
            50247.2695912308,
            53234.1509740724,
            47795.4981056385,
            34853.9582180169,
            37093.6494448758,
            48511.5696679866,
            34868.9383775613,
            36167.2912845567,
        ]
        x_axis = np.linspace(interval[0], interval[1], num=len(y_axis)).tolist()

        signal = pchip(x_axis, y_axis)
        csv_path = self.TEST_DIR / "data" / "pchip_trace.csv"
        csv_data = pd.read_csv(str(csv_path))
        times_col = csv_data.columns[0]
        times = csv_data[times_col].to_numpy()
        sampled_values = np.array(signal.at_times(times))
        signal_col = csv_data.columns[1]

        np.testing.assert_almost_equal(csv_data[signal_col].to_numpy(), sampled_values)

    def test_single_vs_vectorized(self) -> None:
        interval = (0, 100)
        y_axis = [0, 1, 0, 1, 0, 0]
        x_axis = np.linspace(interval[0], interval[1], num=len(y_axis)).tolist()
        times = _random(interval[0], interval[1], len(y_axis))

        signal = pchip(x_axis, y_axis)
        single_sampled_points = [signal.at_time(t) for t in times]
        vector_sampled_points = signal.at_times(times)

        self.assertListEqual(single_sampled_points, vector_sampled_points)

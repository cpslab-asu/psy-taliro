from os import path
from unittest import TestCase

import numpy as np
import numpy.testing
import numpy.random
import pandas as pd
from staliro.core.interval import Interval
from staliro.signals import Pchip, PiecewiseConstant

TEST_DIR = path.dirname(__file__)


def _random(lower: float, upper: float, size: int) -> list[float]:
    rng = np.random.default_rng()
    samples = rng.random(size)

    return [(upper - lower) * sample + lower for sample in samples]


class ConstantSignalTestCase(TestCase):
    def test_constant_interpolator(self) -> None:
        interval = Interval(0, 100)
        y_axis = [0, 1, 0, 1, 0, 0]
        x_axis = np.linspace(interval.lower, interval.upper, num=len(y_axis)).tolist()

        signal = PiecewiseConstant(x_axis, y_axis)
        csv_data = pd.read_csv(path.join(TEST_DIR, "data", "constant_trace.csv"))
        times_col = csv_data.columns[0]
        times = csv_data[times_col].tolist()
        sampled_values = np.array(signal.at_times(times))
        signal_col = csv_data.columns[1]

        np.testing.assert_equal(csv_data[signal_col].to_numpy(), sampled_values)  # type: ignore

    def test_single_vs_vectorized(self) -> None:
        interval = Interval(0, 100)
        y_axis = [0, 1, 0, 1, 0, 0]
        x_axis = np.linspace(interval.lower, interval.upper, num=len(y_axis)).tolist()
        times = _random(interval.lower, interval.upper, len(y_axis))

        signal = PiecewiseConstant(x_axis, y_axis)
        single_sampled_points = [signal.at_time(t) for t in times]
        vector_sampled_points = signal.at_times(times)

        self.assertListEqual(single_sampled_points, vector_sampled_points)


class PchipSignalTestCase(TestCase):
    def test_pchip_interpolator(self) -> None:
        interval = Interval(0, 4)
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
        x_axis = np.linspace(interval.lower, interval.upper, num=len(y_axis)).tolist()

        signal = Pchip(x_axis, y_axis)
        csv_data = pd.read_csv(path.join(TEST_DIR, "data", "pchip_trace.csv"))
        times_col = csv_data.columns[0]
        times = csv_data[times_col].to_numpy()
        sampled_values = np.array(signal.at_times(times))
        signal_col = csv_data.columns[1]

        np.testing.assert_almost_equal(csv_data[signal_col].to_numpy(), sampled_values)  # type: ignore

    def test_single_vs_vectorized(self) -> None:
        interval = Interval(0, 100)
        y_axis = [0, 1, 0, 1, 0, 0]
        x_axis = np.linspace(interval.lower, interval.upper, num=len(y_axis)).tolist()
        times = _random(interval.lower, interval.upper, len(y_axis))

        signal = Pchip(x_axis, y_axis)
        single_sampled_points = [signal.at_time(t) for t in times]
        vector_sampled_points = signal.at_times(times)

        self.assertListEqual(single_sampled_points, vector_sampled_points)

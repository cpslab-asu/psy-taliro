from os import path
from unittest import TestCase

from numpy import array
from numpy.testing import assert_almost_equal, assert_equal
from pandas import read_csv
from staliro.signals import ConstantFactory, PchipFactory

TEST_DIR = path.dirname(__file__)


class ConstantSignalTestCase(TestCase):
    def setUp(self) -> None:
        self.interval = (0, 100)
        self.points = [0, 1, 0, 1, 0, 0]
        self.factory = ConstantFactory()

    def test_axis_generation(self) -> None:
        x_axis = self.factory._x_values(self.interval, len(self.points))
        target = [0, 20, 40, 60, 80, 100]

        assert_equal(x_axis, array(target))

    def test_constant_interpolator(self) -> None:
        interp = self.factory.create(self.interval, array(self.points))
        csv_data = read_csv(path.join(TEST_DIR, "data", "constant_trace.csv"))
        times_col = csv_data.columns[0]
        times = csv_data[times_col].to_numpy()
        signal = array([interp.interpolate(t) for t in times])
        signal_col = csv_data.columns[1]

        assert_equal(csv_data[signal_col].to_numpy(), signal)


class PchipSignalTestCase(TestCase):
    def setUp(self) -> None:
        self.interval = (0, 4)
        self.points = [
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
        self.factory = PchipFactory()

    def test_pchip_interpolator(self) -> None:
        interp = self.factory.create(self.interval, array(self.points))
        csv_data = read_csv(path.join(TEST_DIR, "data", "pchip_trace.csv"))
        times_col = csv_data.columns[0]
        times = csv_data[times_col].to_numpy()
        signal = array([interp.interpolate(t) for t in times])
        signal_col = csv_data.columns[1]

        assert_almost_equal(csv_data[signal_col].to_numpy(), signal)

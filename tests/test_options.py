from unittest import TestCase

import numpy as np

from staliro.core import Interval
from staliro.options import Options, OptionsError, SignalOptions


class SignalOptionsTestCase(TestCase):
    def test_bound_conversion(self) -> None:
        SignalOptions([[1, 2]])
        SignalOptions([(1.0, 2.0)])
        SignalOptions([np.array([1, 2], dtype=np.float32)])

        with self.assertRaises(TypeError):
            SignalOptions({1, 2})  # type: ignore

        with self.assertRaises(TypeError):
            SignalOptions({1: 3, 2: 4})  # type: ignore

        with self.assertRaises(IndexError):
            SignalOptions("a")  # type: ignore

        with self.assertRaises(TypeError):
            SignalOptions(1)  # type: ignore

    def test_signal_times(self) -> None:
        i = [(0, 1)]

        SignalOptions(i, signal_times=np.linspace(0, 10, 10))
        SignalOptions(i, signal_times=[1.0, 2.0, 3.0, 4.0])
        SignalOptions(i, signal_times=(1.0, 2.0, 3.0, 4.0))

        with self.assertRaises(TypeError):
            SignalOptions(i, signal_times="1234")  # type: ignore

        with self.assertRaises(TypeError):
            SignalOptions(i, signal_times={1, 2, 3, 4})  # type: ignore

        with self.assertRaises(TypeError):
            SignalOptions(i, signal_times={1: 2, 3: 4})  # type: ignore


class OptionsTestCast(TestCase):
    def test_static_parameters(self) -> None:
        Options([[1, 2], (3, 4)])
        Options(([1, 2], (3, 4)))

        with self.assertRaises(TypeError):
            Options([{1, 2}, {1: 2, 3: 4}])  # type: ignore

        with self.assertRaises(TypeError):
            Options({1, (3, 4), Interval(5, 6)})  # type: ignore

        with self.assertRaises(TypeError):
            Options({1: [1, 2], 2: (3, 4), 3: Interval(5, 6)})  # type: ignore

    def test_signals(self) -> None:
        Options(signals=[SignalOptions([(0, 1)])])

        with self.assertRaises(TypeError):
            Options(signals=[Interval(0, 1)])  # type: ignore

    def test_runs(self) -> None:
        Options(runs=1)

        with self.assertRaises(TypeError):
            Options(runs=1.0)  # type: ignore

        with self.assertRaises(TypeError):
            Options(runs="a")  # type: ignore

        with self.assertRaises(TypeError):
            Options(runs=[1, 2])  # type: ignore

    def test_parallelization(self) -> None:
        Options(parallelization="all")
        Options(parallelization="cores")
        Options(parallelization=10)

        with self.assertRaises(OptionsError):
            Options(parallelization="foo")  # type: ignore

        with self.assertRaises(OptionsError):
            Options(parallelization=Interval(0, 1))  # type: ignore

        with self.assertRaises(OptionsError):
            Options(parallelization=int)  # type: ignore

from __future__ import annotations

from typing import Sequence, cast
from unittest import TestCase

from staliro.core.interval import Interval
from staliro.core.model import SystemInputs
from staliro.core.sample import Sample
from staliro.core.signal import Signal
from staliro.options import Options, SignalOptions


class SystemInputsTestCase(TestCase):
    def test_decomposition_static(self) -> None:
        param_count = 4
        static_params = [Interval(0.1, 2.0)] * param_count
        options = Options(static_parameters=static_params)
        sample = Sample(range(param_count))
        inputs = SystemInputs(sample, options)

        self.assertEqual(inputs.static, sample.values[0:param_count])

        sample = Sample(range(param_count + 1))
        inputs = SystemInputs(sample, options)

        self.assertEqual(inputs.static, sample.values[0:param_count])
        self.assertNotIn(sample.values[-1], inputs.static)

    def test_decomposition_signals(self) -> None:
        class TestSignal(Signal):
            def __init__(self, xs: Sequence[float], ys: Sequence[float]):
                self.xs = xs
                self.ys = ys

        signals = [
            SignalOptions(interval=Interval(0, 1), factory=TestSignal, control_points=10),
            SignalOptions(interval=Interval(0, 1), factory=TestSignal, control_points=20),
        ]
        param_count = sum(signal.control_points for signal in signals)
        options = Options(signals=signals)
        sample = Sample(range(param_count))
        inputs = SystemInputs(sample, options)
        test_signal1 = cast(TestSignal, inputs.signals[0])
        test_signal2 = cast(TestSignal, inputs.signals[1])

        self.assertEqual(test_signal1.ys, sample.values[0:10])
        self.assertEqual(test_signal2.ys, sample.values[10:30])

        sample = Sample(range(param_count + 1))
        inputs = SystemInputs(sample, options)
        test_signal3 = cast(TestSignal, inputs.signals[0])
        test_signal4 = cast(TestSignal, inputs.signals[1])

        self.assertEqual(test_signal3.ys, sample.values[0:10])
        self.assertEqual(test_signal4.ys, sample.values[10:30])
        self.assertNotIn(sample.values[-1], test_signal3.ys)
        self.assertNotIn(sample.values[-1], test_signal4.ys)


class SystemDataTestCase(TestCase):
    def test_1d_states(self) -> None:
        pass

    def test_2d_states(self) -> None:
        pass

    def test_wrong_dimensions_states(self) -> None:
        pass

    def test_wrong_dimensions_times(self) -> None:
        pass

    def test_extra_arg(self) -> None:
        pass

    def test_no_extra_arg(self) -> None:
        pass

    def test_get_states(self) -> None:
        pass


class SystemFailureTestCase(TestCase):
    def test_extra_arg(self) -> None:
        pass

    def test_no_extra_arg(self) -> None:
        pass

from unittest import TestCase
from typing import Sequence

from staliro.models import (
    StaticParameters,
    SignalTimes,
    SignalValues,
    BlackboxResult,
    blackbox,
    Blackbox,
    InterpolatorBlackbox,
)
from staliro.signals import SignalInterpolator


class ModelTestCase(TestCase):
    def test_blackbox_decorator(self) -> None:
        @blackbox(interpolated=True, sampling_interval=0.2)
        def func1(X: StaticParameters, T: SignalTimes, U: SignalValues) -> BlackboxResult:
            pass

        @blackbox(interpolated=False)
        def func2(X: StaticParameters, U: Sequence[SignalInterpolator]) -> BlackboxResult:
            pass

        self.assertIsInstance(func1, Blackbox)
        self.assertEqual(func1.sampling_interval, 0.2)
        self.assertIsInstance(func2, InterpolatorBlackbox)

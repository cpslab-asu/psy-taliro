from unittest import TestCase

from staliro.models import (
    StaticParameters,
    SignalTimes,
    SignalValues,
    BlackboxResult,
    blackbox,
    _Blackbox,
)


class ModelTestCase(TestCase):
    def test_blackbox_decorator(self) -> None:
        @blackbox(sampling_interval=0.2)
        def func1(
            params: StaticParameters, times: SignalTimes, signals: SignalValues
        ) -> BlackboxResult:
            pass

        self.assertIsInstance(func1, _Blackbox)
        self.assertEqual(func1.sampling_interval, 0.2)

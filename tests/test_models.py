from unittest import TestCase

from staliro.models import (
    StaticParameters,
    SignalTimes,
    SignalValues,
    BlackboxResult,
    blackbox,
    Blackbox,
)


class ModelTestCase(TestCase):
    def test_blackbox_decorator_args(self) -> None:
        @blackbox(sampling_interval=0.2)
        def dummy(
            params: StaticParameters, times: SignalTimes, signals: SignalValues
        ) -> BlackboxResult:
            pass

        self.assertIsInstance(dummy, Blackbox)
        self.assertEqual(dummy.sampling_interval, 0.2)

    def test_blackbox_decorator_no_args(self) -> None:
        @blackbox
        def dummy(
            params: StaticParameters, times: SignalTimes, signals: SignalValues
        ) -> BlackboxResult:
            pass

        self.assertIsInstance(dummy, Blackbox)
        self.assertEqual(dummy.sampling_interval, 0.1)

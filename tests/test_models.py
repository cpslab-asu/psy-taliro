from typing import Any
from unittest import TestCase
from unittest.mock import Mock, NonCallableMock

from numpy import ndarray
from numpy.typing import NDArray

from staliro.core.interval import Interval
from staliro.core.model import ModelData
from staliro.core.signal import Signal
from staliro.models import (
    ODE,
    Blackbox,
    SignalTimes,
    SignalValues,
    State,
    StaticInput,
    blackbox,
    ode,
)

AnyData = ModelData[Any, Any]


class BlackboxTestCase(TestCase):
    def test_simulation(self) -> None:
        sampling_interval = 0.1
        func = Mock(return_value=NonCallableMock(spec=ModelData))
        model: Blackbox[Any, Any] = Blackbox(func, sampling_interval=sampling_interval)

        static_inputs = [1, 2, 3, 4]
        signals = [Mock(spec=Signal), Mock(spec=Signal)]
        interval = Interval(0, 10)

        result = model.simulate(static_inputs, signals, interval)

        for signal in signals:
            self.assertEqual(signal.at_times.call_count, 1)

        func.assert_called_once()

        fn_args, fn_kwargs = func.call_args
        fn_static_inputs, signal_times, signal_traces = fn_args
        expected_n_points = int(interval.length / sampling_interval)

        self.assertEqual(result, func.return_value)
        self.assertListEqual(static_inputs, fn_static_inputs)

        self.assertIsInstance(signal_times, ndarray)
        self.assertEqual(signal_times.ndim, 1)
        self.assertEqual(signal_times.size, expected_n_points)

        self.assertIsInstance(signal_traces, ndarray)
        self.assertEqual(signal_traces.shape[0], len(signals))

        for signal, signal_trace in zip(signals, signal_traces):
            self.assertEqual(signal_trace, signal.at_times.return_value)


class BlackboxDecoratorTestCase(TestCase):
    def test_with_args(self) -> None:
        @blackbox(sampling_interval=0.2)
        def dummy(static: StaticInput, times: SignalTimes, signals: SignalValues) -> AnyData:
            ...

        self.assertIsInstance(dummy, Blackbox)
        self.assertEqual(dummy.sampling_interval, 0.2)

    def test_without_args(self) -> None:
        @blackbox
        def dummy(static: StaticInput, times: SignalTimes, signals: SignalValues) -> AnyData:
            ...

        self.assertIsInstance(dummy, Blackbox)
        self.assertEqual(dummy.sampling_interval, 0.1)


class ODEDecoratorTestCase(TestCase):
    def test_with_args(self) -> None:
        @ode(method="RK23")
        def dummy(time: float, state: State, signals: NDArray[Any]) -> State:
            ...

        self.assertIsInstance(dummy, ODE)
        self.assertEqual(dummy.method, "RK23")

    def test_without_args(self) -> None:
        @ode
        def dummy(time: float, state: State, signals: NDArray[Any]) -> State:
            ...

        self.assertIsInstance(dummy, ODE)
        self.assertEqual(dummy.method, "RK45")

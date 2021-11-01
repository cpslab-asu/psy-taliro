from unittest import TestCase
from unittest.mock import Mock, NonCallableMock, patch

from staliro.core import Model, Optimizer, Specification
from staliro.core.cost import SignalParameters
from staliro.options import Options, SignalOptions
from staliro.staliro import staliro


class StaliroTestCase(TestCase):
    @patch("staliro.staliro.Scenario")
    def test_static_parameters(self, scenario_mock: Mock) -> None:
        model = NonCallableMock(spec=Model)
        specification = NonCallableMock(spec=Specification)
        optimizer = NonCallableMock(spec=Optimizer)

        static_inputs = [(0, 1), (10, 12), (3, 4)]
        options = Options(runs=1, iterations=10, static_parameters=static_inputs)

        staliro(model, specification, optimizer, options)

        scenario_mock.assert_called_once()
        args, kwargs = scenario_mock.call_args

        self.assertEqual(kwargs["static_parameter_range"], slice(0, 3, 1))

        pass

    @patch("staliro.staliro.Scenario")
    def test_signals(self, scenario_mock: Mock) -> None:
        model = NonCallableMock(spec=Model)
        specification = NonCallableMock(spec=Specification)
        optimizer = NonCallableMock(spec=Optimizer)

        static_inputs = [(0, 1), (10, 12), (3, 4)]
        signals = [SignalOptions((0, 100), control_points=7)]
        options = Options(runs=1, iterations=10, static_parameters=static_inputs, signals=signals)

        staliro(model, specification, optimizer, options)

        scenario_mock.assert_called_once()
        args, kwargs = scenario_mock.call_args
        signal_params: list[SignalParameters] = kwargs["signal_parameters"]

        self.assertEqual(len(signal_params), len(signals))
        self.assertEqual(signal_params[0].values_range, slice(3, 10, 1))

        pass

from unittest import TestCase
from unittest.mock import Mock, NonCallableMock, patch

from staliro.core import Model, Optimizer, Specification
from staliro.core.layout import SampleLayout
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
        _, kwargs = scenario_mock.call_args
        layout: SampleLayout = kwargs["layout"]

        self.assertEqual(layout.static_parameters, slice(0, 3, 1))

        pass

    @patch("staliro.staliro.Scenario")
    def test_signals(self, scenario_mock: Mock) -> None:
        model = NonCallableMock(spec=Model)
        specification = NonCallableMock(spec=Specification)
        optimizer = NonCallableMock(spec=Optimizer)

        static_inputs = [(0, 1), (10, 12), (3, 4)]
        signals = [SignalOptions(control_points=[(0, 100)] * 7)]
        options = Options(runs=1, iterations=10, static_parameters=static_inputs, signals=signals)

        staliro(model, specification, optimizer, options)

        scenario_mock.assert_called_once()
        _, kwargs = scenario_mock.call_args
        layout: SampleLayout = kwargs["layout"]

        self.assertEqual(len(layout.signals), len(signals))
        self.assertNotEqual(layout.signals.get((3, 10)), None)

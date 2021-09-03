from __future__ import annotations

import math
from typing import Any
from unittest import TestCase
from unittest.mock import MagicMock, NonCallableMagicMock, NonCallableMock, PropertyMock, patch

from staliro.core.cost import CostFn, Thunk, Evaluation, TimingData
from staliro.core.model import Model, SystemData, SystemFailure, SystemInputs
from staliro.core.sample import Sample
from staliro.core.specification import Specification
from staliro.options import Options


class TimingDataTestCase(TestCase):
    def test_total_time(self) -> None:
        self.assertEqual(TimingData(10.0, 10.0).total, 20)


class ThunkTestCase(TestCase):
    def test_specification_callable(self) -> None:
        sample = MagicMock()
        specification = MagicMock()
        thunk: Thunk[Any] = Thunk(sample, MagicMock(), specification, MagicMock())

        thunk.specification

        specification.assert_called_once_with(sample)

    def test_specification_value(self) -> None:
        specification = NonCallableMagicMock()
        thunk: Thunk[Any] = Thunk(MagicMock(), MagicMock(), specification, MagicMock())

        thunk.specification

        specification.assert_not_called()

    def test_evaluate_data(self) -> None:
        sample = MagicMock(spec=Sample)
        inputs = MagicMock(spec=SystemInputs)
        options = MagicMock(spec=Options)

        data = MagicMock(spec=SystemData)
        model = MagicMock(spec=Model)
        model.simulate = MagicMock(return_value=data)

        cost = MagicMock()
        spec = NonCallableMagicMock(spec=Specification)
        spec.evaluate = MagicMock(return_value=cost)

        with patch("staliro.core.cost.Thunk.system_inputs", new_callable=PropertyMock) as mock:
            mock.return_value = inputs

            thunk: Thunk[Any] = Thunk(sample, model, spec, options)
            result = thunk.evaluate()

            mock.assert_called_once()

        model.simulate.assert_called_once_with(inputs, options.interval)
        spec.evaluate.assert_called_once_with(data.states, data.times)

        self.assertIsInstance(result, Evaluation)
        self.assertEqual(result.sample, sample)
        self.assertEqual(result.cost, cost)
        self.assertIsInstance(result.timing, TimingData)

    def test_evaluate_failure(self) -> None:
        sample = MagicMock(spec=Sample)
        inputs = MagicMock(spec=SystemInputs)
        options = MagicMock(spec=Options)

        failure = MagicMock(spec=SystemFailure)
        model = MagicMock(spec=Model)
        model.simulate = MagicMock(return_value=failure)

        spec = MagicMock(spec=Specification)
        spec.evaluate = MagicMock()

        with patch("staliro.core.cost.Thunk.system_inputs", new_callable=PropertyMock) as mock:
            mock.return_value = inputs

            thunk: Thunk[Any] = Thunk(sample, model, spec, options)
            result = thunk.evaluate()

            mock.assert_called_once()

        model.simulate.assert_called_once_with(inputs, options.interval)
        spec.evaluate.assert_not_called()

        self.assertIsInstance(result, Evaluation)
        self.assertEqual(result.sample, sample)
        self.assertEqual(result.cost, -math.inf)
        self.assertIsInstance(result.timing, TimingData)


class CostFnTestCase(TestCase):
    def test_eval_sample(self) -> None:
        model = MagicMock(spec=Model)
        model.simulate = MagicMock(return_value=MagicMock(spec=SystemData))
        spec = NonCallableMock(spec=Specification)
        options = MagicMock(spec=Options)
        cost_fn: CostFn[Any] = CostFn(model, spec, options)

        sample = MagicMock(spec=Sample)
        cost_fn.eval_sample(sample)

        self.assertEqual(len(cost_fn.history), 1)

    def test_eval_samples(self) -> None:
        model = MagicMock(spec=Model)
        model.simulate = MagicMock(return_value=MagicMock(spec=SystemData))
        spec = NonCallableMock(spec=Specification)
        options = MagicMock(spec=Options)
        cost_fn: CostFn[Any] = CostFn(model, spec, options)

        samples = [MagicMock(spec=Sample)] * 10
        cost_fn.eval_samples(samples)

        self.assertEqual(len(cost_fn.history), 10)

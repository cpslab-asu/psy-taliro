from __future__ import annotations

from math import inf
from typing import Any
from unittest import TestCase, skip
from unittest.mock import Mock, NonCallableMock

from staliro.core.cost import (
    CostFn,
    SpecificationFactory,
    Thunk,
    Evaluation,
    TimingData,
    SignalParameters,
    decompose_sample,
)
from staliro.core.interval import Interval
from staliro.core.model import Failure, Model, ModelData
from staliro.core.sample import Sample
from staliro.core.specification import Specification, SpecificationError


class TimingDataTestCase(TestCase):
    def test_total_time(self) -> None:
        self.assertEqual(TimingData(10.0, 10.0).total, 20)


class ThunkTestCase(TestCase):
    def setUp(self) -> None:
        self.sample = Sample([1, 2, 3, 4])
        self.model = NonCallableMock(spec=Model)
        self.interval = Interval(0, 1)
        self.static_parameter_range = slice(0, 2, 1)
        self.signal_parameters = [
            SignalParameters(values_range=slice(2, 4, 1), times=[1.0, 2.0], factory=Mock())
        ]

    def test_specification_noncallable(self) -> None:
        specification: Specification[Any] = NonCallableMock(spec=Specification)
        thunk: Thunk[Any, Any] = Thunk(
            self.sample,
            self.model,
            specification,
            self.interval,
            self.static_parameter_range,
            self.signal_parameters,
        )

        self.assertEqual(thunk.specification, specification)

    def test_specification_callable(self) -> None:
        specification: Specification[Any] = NonCallableMock(spec=Specification)
        specification_factory: SpecificationFactory[Any] = Mock(return_value=specification)
        thunk: Thunk[Any, Any] = Thunk(
            self.sample,
            self.model,
            specification_factory,
            self.interval,
            self.static_parameter_range,
            self.signal_parameters,
        )

        factory_result = thunk.specification

        specification_factory.assert_called_once()  # type: ignore
        specification_factory.assert_called_with(self.sample)  # type: ignore
        self.assertEqual(factory_result, specification)

    def test_specification_callable_return_type(self) -> None:
        bad_factory = Mock(return_value=None)
        thunk: Thunk[Any, Any] = Thunk(
            self.sample,
            self.model,
            bad_factory,
            self.interval,
            self.static_parameter_range,
            self.signal_parameters,
        )

        with self.assertRaises(SpecificationError):
            thunk.specification

    def test_data_evaluation(self) -> None:
        model_result = NonCallableMock(spec=ModelData)
        model = NonCallableMock(spec=Model)
        model.simulate = Mock(return_value=model_result)

        specification = NonCallableMock(spec=Specification)
        specification.evaluate = Mock(return_value=0)

        thunk: Thunk[Any, Any] = Thunk(
            self.sample,
            model,
            specification,
            self.interval,
            self.static_parameter_range,
            self.signal_parameters,
        )

        evaluation = thunk.evaluate()
        static_parameters, signals = decompose_sample(
            self.sample, self.static_parameter_range, self.signal_parameters
        )

        model.simulate.assert_called_once()
        model.simulate.assert_called_with(static_parameters, signals, self.interval)
        specification.evaluate.assert_called_once()
        specification.evaluate.assert_called_with(model_result.states, model_result.times)

        self.assertIsInstance(evaluation, Evaluation)
        self.assertEqual(evaluation.cost, 0)
        self.assertEqual(evaluation.sample, self.sample)

    def test_failure_evaluation(self) -> None:
        model_result = NonCallableMock(spec=Failure)
        model = NonCallableMock(spec=Model)
        model.simulate = Mock(return_value=model_result)

        specification = NonCallableMock(spec=Specification)
        specification.evaluate = Mock(return_value=0)

        thunk: Thunk[Any, Any] = Thunk(
            self.sample,
            model,
            specification,
            self.interval,
            self.static_parameter_range,
            self.signal_parameters,
        )

        evaluation = thunk.evaluate()
        static_parameters, signals = decompose_sample(
            self.sample, self.static_parameter_range, self.signal_parameters
        )

        model.simulate.assert_called_once()
        model.simulate.assert_called_with(static_parameters, signals, self.interval)
        specification.evaluate.assert_not_called()

        self.assertIsInstance(evaluation, Evaluation)
        self.assertEqual(evaluation.cost, -inf)
        self.assertEqual(evaluation.sample, self.sample)


class CostFnTestCase(TestCase):
    def setUp(self) -> None:
        self.model = NonCallableMock(spec=Model)
        self.model.simulate = Mock(return_value=NonCallableMock(spec=ModelData))
        self.specification = NonCallableMock(spec=Specification)
        self.interval = Interval(0, 1)
        self.static_parameter_range = slice(0, 2, 1)
        self.signal_parameters = [
            SignalParameters(values_range=slice(2, 4, 1), times=[1.0, 2.0], factory=Mock())
        ]
        self.cost_fn: CostFn[Any, Any] = CostFn(
            self.model,
            self.specification,
            self.interval,
            self.static_parameter_range,
            self.signal_parameters,
        )

    def test_eval_sample(self) -> None:
        sample = Sample([1, 2, 3, 4])
        cost = self.cost_fn.eval_sample(sample)

        self.model.simulate.assert_called_once()
        self.specification.evaluate.assert_called_once()

        self.assertEqual(cost, self.specification.evaluate.return_value)

        self.assertEqual(len(self.cost_fn.history), 1)
        self.assertEqual(self.cost_fn.history[0].sample, sample)

    def test_eval_samples(self) -> None:
        samples = [Sample([1, 2, 3, 4]), Sample([5, 6, 7, 8])]
        costs = self.cost_fn.eval_samples(samples)

        self.model.simulate.assert_called()
        self.assertEqual(self.model.simulate.call_count, 2)

        self.specification.evaluate.assert_called()
        self.assertEqual(self.specification.evaluate.call_count, 2)

        self.assertListEqual(costs, [self.specification.evaluate.return_value] * 2)

        self.assertEqual(len(self.cost_fn.history), 2)
        self.assertEqual(self.cost_fn.history[0].sample, samples[0])
        self.assertEqual(self.cost_fn.history[1].sample, samples[1])

    def test_eval_samples_parallel(self) -> None:
        samples = [Sample([1, 2, 3, 4]), Sample([5, 6, 7, 8])]
        costs = self.cost_fn.eval_samples_parallel(samples, processes=1)

        self.model.simulate.assert_called()
        self.assertEqual(self.model.simulate.call_count, 2)

        self.specification.evaluate.assert_called()
        self.assertEqual(self.specification.evaluate.call_count, 2)

        self.assertListEqual(costs, [self.specification.evaluate.return_value] * 2)

        self.assertEqual(len(self.cost_fn.history), 2)
        self.assertEqual(self.cost_fn.history[0].sample, samples[0])
        self.assertEqual(self.cost_fn.history[1].sample, samples[1])

    def test_single_vs_many_samples(self) -> None:
        samples = [Sample([1, 2, 3, 4]), Sample([5, 6, 7, 8])]
        single_cost_fn: CostFn[Any, Any] = CostFn(
            self.model,
            self.specification,
            self.interval,
            self.static_parameter_range,
            self.signal_parameters,
        )
        many_cost_fn: CostFn[Any, Any] = CostFn(
            self.model,
            self.specification,
            self.interval,
            self.static_parameter_range,
            self.signal_parameters,
        )
        parallel_cost_fn: CostFn[Any, Any] = CostFn(
            self.model,
            self.specification,
            self.interval,
            self.static_parameter_range,
            self.signal_parameters,
        )

        single_costs = [single_cost_fn.eval_sample(sample) for sample in samples]
        many_costs = many_cost_fn.eval_samples(samples)
        parallel_costs = parallel_cost_fn.eval_samples_parallel(samples, processes=1)

        self.assertListEqual(single_cost_fn.history, many_cost_fn.history)
        self.assertListEqual(many_cost_fn.history, parallel_cost_fn.history)

        self.assertListEqual(single_costs, many_costs)
        self.assertListEqual(many_costs, parallel_costs)

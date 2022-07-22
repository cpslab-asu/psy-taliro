from __future__ import annotations

from unittest import TestCase

from staliro.core.cost import Evaluation, TimingData
from staliro.core.interval import Interval
from staliro.core.result import Result, Run, TimeStats
from staliro.core.sample import Sample


class TimingStatsTestCase(TestCase):
    def setUp(self) -> None:
        self.stats = TimeStats([1, 2, 3])

    def test_total(self) -> None:
        self.assertEqual(self.stats.total_duration, 6)

    def test_average(self) -> None:
        self.assertEqual(self.stats.avg_duration, 2)

    def test_max(self) -> None:
        self.assertEqual(self.stats.max_duration, 3)

    def test_min(self) -> None:
        self.assertEqual(self.stats.min_duration, 1)


class RunTestCase(TestCase):
    def setUp(self) -> None:
        self.history = [
            Evaluation(cost, Sample([]), [], [], None, TimingData(cost, 0)) for cost in range(1, 7)
        ]

    def test_worst_eval(self) -> None:
        run = Run(None, self.history, 0, 0)
        worst_eval = run.worst_eval

        self.assertIsInstance(worst_eval, Evaluation)
        self.assertEqual(worst_eval.cost, 6)

    def test_best_eval(self) -> None:
        run = Run(None, self.history, 0, 0)
        best_eval = run.best_eval

        self.assertIsInstance(best_eval, Evaluation)
        self.assertEqual(best_eval.cost, 1)

    def test_fastest_eval(self) -> None:
        run = Run(None, self.history, 0, 0)
        fastest_eval = run.fastest_eval

        self.assertIsInstance(fastest_eval, Evaluation)
        self.assertEqual(fastest_eval.timing.total, 1)

    def test_slowest_eval(self) -> None:
        run = Run(None, self.history, 0, 0)
        slowest_eval = run.slowest_eval

        self.assertIsInstance(slowest_eval, Evaluation)
        self.assertEqual(slowest_eval.timing.total, 6)


class ResultTestCase(TestCase):
    def setUp(self) -> None:
        def run(multiplier: float) -> Run[None, None]:
            history = [
                Evaluation(cost, Sample([]), [], [], None, TimingData(cost, 0))
                for cost in range(1, 7)
            ]
            return Run(None, history, 0, 0)

        factors = range(1, 4)
        self.runs = [run(factor) for factor in factors]

    def test_worst_run(self) -> None:
        result = Result(self.runs, Interval(0, 1), 0, None)
        costs = [evaluation.cost for run in self.runs for evaluation in run.history]
        worst_run = result.worst_run

        self.assertIsInstance(worst_run, Run)
        self.assertEqual(worst_run.worst_eval.cost, max(costs))

    def test_best_run(self) -> None:
        result = Result(self.runs, Interval(0, 1), 0, None)
        costs = [evaluation.cost for run in self.runs for evaluation in run.history]
        best_run = result.best_run

        self.assertIsInstance(best_run, Run)
        self.assertEqual(best_run.best_eval.cost, min(costs))

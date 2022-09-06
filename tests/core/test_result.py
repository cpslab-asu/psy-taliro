from __future__ import annotations

from unittest import TestCase

from staliro.core.cost import Evaluation, TimingData
from staliro.core.result import Run, TimeStats
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
            Evaluation(cost, Sample([]), None, TimingData(cost, 0)) for cost in range(1, 7)
        ]

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

from __future__ import annotations

from unittest import TestCase

from staliro.core.interval import Interval


class IntervalTestCase(TestCase):
    def test_int_bound(self) -> None:
        interval = Interval(0, 1)

        self.assertIsInstance(interval.lower, float)
        self.assertIsInstance(interval.upper, float)

    def test_float_bound(self) -> None:
        interval = Interval(0.0, 1.0)

        self.assertIsInstance(interval.lower, float)
        self.assertIsInstance(interval.upper, float)

    def test_nonnumeric_bound(self) -> None:
        with self.assertRaises(TypeError):
            Interval([1, 2], "b")  # type: ignore

    def test_bounds_order(self) -> None:
        with self.assertRaises(ValueError):
            Interval(1, 1)
            Interval(1, 0)

    def test_tuple_conversion(self) -> None:
        interval = Interval(0, 1)
        astuple = interval.astuple()

        self.assertIsInstance(astuple, tuple)
        self.assertEqual(astuple[0], interval.lower)
        self.assertEqual(astuple[1], interval.upper)

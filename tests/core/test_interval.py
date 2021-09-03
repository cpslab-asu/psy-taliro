from __future__ import annotations

from unittest import TestCase

from staliro.core.interval import Interval


class IntervalTestCase(TestCase):
    def test_arg_types(self) -> None:
        Interval(1, 2)
        Interval(1.0, 2.0)
        Interval(1, 2.0)
        Interval(1.0, 2)

        with self.assertRaises(TypeError):
            Interval("a", "b")  # type: ignore
            Interval([1, 2], 3)  # type: ignore
            Interval(2, {1, 2})  # type: ignore
            Interval(["a", "b"])  # type: ignore
            Interval({"a": 1, "b": 2})  # type: ignore
            Interval(["a", "b"], "c")  # type: ignore
            Interval("a", ["b", "c"])  # type: ignore

    def test_arg_order(self) -> None:
        with self.assertRaises(ValueError):
            Interval(2, 1)

    def test_attributes(self) -> None:
        interval = Interval(1, 2.0)

        self.assertEqual(interval.lower, 1.0)
        self.assertEqual(interval.upper, 2.0)
        self.assertEqual(interval.length, 1.0)

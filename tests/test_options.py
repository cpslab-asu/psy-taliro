from unittest import TestCase

from staliro.options import StaliroOptions, SignalOptions, Interval


class IntervalTestCase(TestCase):
    def test_tuple(self):
        interval = Interval((0, 1))

        self.assertEqual(interval.lower, 0)
        self.assertEqual(interval.upper, 1)

    def test_list(self):
        interval = Interval([0, 1])

        self.assertEqual(interval.lower, 0)
        self.assertEqual(interval.upper, 1)

    def test_interval(self):
        interval = Interval(Interval((0, 1)))

        self.assertEqual(interval.lower, 0)
        self.assertEqual(interval.upper, 1)

    def test_not_iterable(self):
        with self.assertRaises(TypeError):
            Interval(1)

    def test_wrong_length(self):
        with self.assertRaises(ValueError):
            Interval((1,))

    def test_descending_order(self):
        with self.assertRaises(ValueError):
            Interval((1, 0))


class StaliroOptionsTestCase(TestCase):
    def test_bounds_length(self):
        options = StaliroOptions(
            static_parameters=[(0, 1), (0, 1)],
            signals=[SignalOptions(interval=(0, 1), control_points=10)],
        )

        self.assertEqual(len(options.bounds), 12)


class SignalOptionsTestCase(TestCase):
    def test_bounds_length(self):
        options = SignalOptions(interval=(0, 1), control_points=10)
        self.assertEqual(len(options.bounds), 10)

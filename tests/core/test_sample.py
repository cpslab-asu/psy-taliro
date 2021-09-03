from __future__ import annotations

from unittest import TestCase

from staliro.core.sample import Sample


class SampleTestCase(TestCase):
    def test_args(self) -> None:
        Sample([1, 2, 3, 4])
        Sample((1, 2, 3, 4))
        Sample({1, 2, 3, 4})

        with self.assertRaises(TypeError):
            Sample(1)  # type: ignore
            Sample("abc")  # type: ignore

    def test_getitem(self) -> None:
        sample = Sample([1, 2, 3, 4])

        self.assertEqual(sample[0], 1.0)
        self.assertEqual(sample[0:2], [1.0, 2.0])

    def test_len(self) -> None:
        self.assertEqual(len(Sample([1, 2, 3, 4])), 4)

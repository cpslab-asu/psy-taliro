from __future__ import annotations

from unittest import TestCase

import numpy as np
import numpy.testing
import staliro.core.model as model


class ModelData(TestCase):
    def setUp(self) -> None:
        self.timestamps = np.array([1, 2, 3], dtype=np.float32)
        self.trajectories1d = np.array([1, 2, 3])
        self.trajectories2d = np.array([self.trajectories1d, self.trajectories1d])

    def test_without_extra(self) -> None:
        data = model.ModelData(self.trajectories2d, self.timestamps)

        self.assertIsInstance(data, model.ModelData)
        np.testing.assert_equal(data.states, self.trajectories2d)  # type: ignore
        np.testing.assert_equal(data.times, self.timestamps)  # type: ignore
        self.assertIsNone(data.extra)

    def test_with_extra(self) -> None:
        data = model.ModelData(self.trajectories2d, self.timestamps, "foo")

        self.assertIsInstance(data, model.ModelData)
        self.assertEqual(data.extra, "foo")

    def test_timestamp_types(self) -> None:
        with self.assertRaises(TypeError):
            model.ModelData(self.trajectories1d, [1, 2, 3])
            model.ModelData(self.trajectories1d, (1, 2, 3))


class SystemFailureTestCase(TestCase):
    def test_extra_arg(self) -> None:
        failure = model.Failure()

        self.assertIsInstance(failure, model.Failure)
        self.assertIsNone(failure.extra)

    def test_no_extra_arg(self) -> None:
        failure = model.Failure("foo")

        self.assertIsInstance(failure, model.Failure)
        self.assertEqual(failure.extra, "foo")

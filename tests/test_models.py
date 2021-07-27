from typing import Any
from unittest import TestCase

import numpy as np
import staliro.models as models


class BlackboxDecoratorTestCase(TestCase):
    def test_with_args(self) -> None:
        @models.blackbox(sampling_interval=0.2)
        def dummy(
            params: models.StaticParameters, times: models.SignalTimes, signals: models.SignalValues
        ) -> models.ModelResult[Any]:
            pass

        self.assertIsInstance(dummy, models.Blackbox)
        self.assertEqual(dummy.sampling_interval, 0.2)

    def test_without_args(self) -> None:
        @models.blackbox
        def dummy(
            params: models.StaticParameters, times: models.SignalTimes, signals: models.SignalValues
        ) -> models.ModelResult[Any]:
            pass

        self.assertIsInstance(dummy, models.Blackbox)
        self.assertEqual(dummy.sampling_interval, 0.1)


class SimulationResultTestCase(TestCase):
    def setUp(self) -> None:
        self.timestamps = np.array([1, 2, 3])
        self.trajectories1d = np.array([1, 2, 3])
        self.trajectories2d = np.array([self.trajectories1d, self.trajectories1d])

    def test_shape_validation(self) -> None:
        self.assertIsInstance(
            models.SimulationResult(self.trajectories1d, self.timestamps), models.SimulationResult
        )
        self.assertIsInstance(
            models.SimulationResult(self.trajectories2d, self.timestamps), models.SimulationResult
        )
        self.assertIsInstance(
            models.SimulationResult(self.trajectories2d.T, self.timestamps), models.SimulationResult
        )

        with self.assertRaises(ValueError):
            models.SimulationResult(
                np.array([self.trajectories2d, self.trajectories2d]), self.timestamps
            )
            models.SimulationResult(
                self.trajectories2d, np.array([self.timestamps, self.timestamps])
            )
            models.SimulationResult(self.trajectories2d, np.array([1, 2, 3, 4]))

    def test_without_extra(self) -> None:
        self.assertIsInstance(
            models.SimulationResult(self.trajectories2d, self.timestamps), models.SimulationResult
        )

    def test_with_extra(self) -> None:
        self.assertIsInstance(
            models.SimulationResult(self.trajectories2d, self.timestamps, "foo"),
            models.SimulationResult,
        )

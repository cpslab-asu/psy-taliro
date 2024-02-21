from pathlib import Path
from unittest import TestCase

import numpy as np
import pandas as pd

from staliro.specifications import RTAMTDense, RTAMTDiscrete

SIG_FIGS = 3


class SpecificationTestCase(TestCase):
    def setUp(self) -> None:
        # The requirements are the same; however, they defer in the syntax since TLTK currently
        # uses the older parsing method of passing predicate names rather than expressions.
        self._requirement = "(not ((always[0.0, 4.0]((x1 <= 250.0) and (x1 >= 240.0))) and (eventually[3.5,4.0]((x1 <= 240.1) and (x1 >= 240.0)))))"
        self._expected_robustness = -0.0160623609618824

        # trajectory data
        csv_path = Path(__file__).parent / "data" / "trajectory.csv"
        self._data = pd.read_csv(str(csv_path))

    def test_rtamt_discrete_specification(self) -> None:
        predicates = {"x1": 0}
        specification = RTAMTDiscrete(self._requirement, predicates)

        timestamps = self._data["t"].to_numpy(dtype=np.float64).tolist()
        trajectories = self._data["x1"].to_numpy(dtype=np.float64).tolist()
        robustness = specification.evaluate(np.atleast_2d(trajectories), timestamps)

        self.assertAlmostEqual(robustness, self._expected_robustness, SIG_FIGS)

    def test_rtamt_dense_specification(self) -> None:
        predicates = {"x1": 0}
        specification = RTAMTDense(self._requirement, predicates)

        timestamps = self._data["t"].to_numpy(dtype=np.float64).tolist()
        trajectories = self._data["x1"].to_numpy(dtype=np.float64).tolist()
        robustness = specification.evaluate(np.atleast_2d(trajectories), timestamps)

        self.assertAlmostEqual(robustness, self._expected_robustness, SIG_FIGS)

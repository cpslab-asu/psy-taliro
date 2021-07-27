from os import path
from unittest import TestCase

from numpy import float32, float64, atleast_2d
from pandas import read_csv
from staliro.specification import TLTK, RTAMTDiscrete, RTAMTDense, PredicateProps

SIG_FIGS = 3


class SpecificationTestCase(TestCase):
    def setUp(self) -> None:
        # The requirements are the same; however, they defer in the syntax since TLTK currently
        # uses the older parsing method of passing predicate names rather than expressions.
        self._requirement = "(not ((always[0.0, 4.0]((x1 <= 250.0) and (x1 >= 240.0))) and (eventually[3.5,4.0]((x1 <= 240.1) and (x1 >= 240.0)))))"
        self._expected_robustness = -0.0160623609618824

        # trajectory data
        testdir = path.dirname(path.realpath(__file__))
        self._data = read_csv(path.join(testdir, "data", "trajectory.csv"))

    def test_tltk_specification(self) -> None:
        predicates = {"x1": PredicateProps(0)}
        specification = TLTK(self._requirement, predicates)

        timestamps = self._data["t"].to_numpy(dtype=float32)
        trajectories = self._data[["x1"]].to_numpy()
        robustness = specification.evaluate(atleast_2d(trajectories).T, timestamps)

        self.assertAlmostEqual(robustness, self._expected_robustness, SIG_FIGS)

    def test_rtamt_discrete_specification(self) -> None:
        predicates = {"x1": PredicateProps(0, "float")}
        specification = RTAMTDiscrete(self._requirement, predicates)

        timestamps = self._data["t"].to_numpy(dtype=float64)
        trajectories = self._data["x1"].to_numpy(dtype=float64)
        robustness = specification.evaluate(atleast_2d(trajectories), timestamps)

        self.assertAlmostEqual(robustness, self._expected_robustness, SIG_FIGS)

    def test_rtamt_dense_specification(self) -> None:
        predicates = {"x1": PredicateProps(0, "float")}
        specification = RTAMTDense(self._requirement, predicates)

        timestamps = self._data["t"].to_numpy(dtype=float64)
        trajectories = self._data["x1"].to_numpy(dtype=float64)
        robustness = specification.evaluate(atleast_2d(trajectories), timestamps)

        self.assertAlmostEqual(robustness, self._expected_robustness, SIG_FIGS)

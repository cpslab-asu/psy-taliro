from os import path
from unittest import TestCase

from numpy import float32, float64
from pandas import read_csv
from staliro.specification import TLTK, RTAMTDiscrete, RTAMTDense, Predicate


class SpecificationTestCase(TestCase):
    def setUp(self) -> None:
        # The requirements are the same; however, they defer in the syntax since TLTK currently
        # uses the older parsing method of passing predicate names rather than expressions.
        self._tltk_formula = "!(([][0,4.0] a) /\ (<>[3.5,4.0] b))"
        self._rtamt_formula = "(not ((always[0.0:4.0]((x1 <= 250) and (x1 >= 240))) and (eventually[3.5,4.0]((x1 <= 240.1) and (x1 >= 240.0)))))"

        self._expected_robustness = -0.0160623609618824

        # trajectory data
        testdir = path.dirname(path.realpath(__file__))
        self._data = read_csv(path.join(testdir, "data", "trajectory.csv"))

    def test_tltk_specification(self) -> None:
        predicates = {"a": Predicate(0), "b": Predicate(0)}
        specification = TLTK(self._tltk_formula, predicates)

        timestamps = self._data["t"].to_numpy(dtype=float32)
        trajectory = self._data[["x1", "x2", "x3"]].to_numpy()
        robustness = specification.evaluate(trajectory, timestamps)

        self.assertAlmostEqual(robustness, self._expected_robustness)

    def test_rtamt_discrete_specification(self) -> None:
        predicates = {"x1": Predicate(0, "float")}
        specification = RTAMTDiscrete(self._rtamt_formula, predicates)

        timestamps = self._data["t"].to_numpy(dtype=float64)
        trajectories = self._data["x1"].to_numpy(dtype=float64)
        robustness = specification.evaluate(trajectories, timestamps)

        self.assertAlmostEqual(robustness, self._expected_robustness)

    def test_rtamt_dense_specification(self) -> None:
        predicates = {"x1": Predicate(0, "float")}
        specification = RTAMTDense(self._rtamt_formula, predicates)

        timestamps = self._data["t"].to_numpy(dtype=float64)
        trajectories = self._data["x1"].to_numpy(dtype=float64)
        robustness = specification.evaluate(trajectories, timestamps)

        self.assertAlmostEqual(robustness, self._expected_robustness)

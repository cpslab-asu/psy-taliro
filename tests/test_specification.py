from os import path
from unittest import TestCase

import numpy as np
import pandas as pd
import tltk_mtl as mtl
from staliro.specification import Specification, Subsystem


class SpecificationTestCase(TestCase):
    def setUp(self) -> None:
        # The requirements are the same; however, they defer in the syntax since TLTK currently
        # uses the older parsing method of passing predicate names rather than expressions.
        self._tltk_formula = "!(([][0,4.0] a) /\ (<>[3.5,4.0] b))"
        self._rtamt_formula = "(not ((always[0.0:4.0]((x1 <= 250) and (x1 >= 240))) and (eventually[3.5,4.0]((x1 <= 240.1) and (x1 >= 240.0)))))"

        self._expected_robustness = -0.0160623609618824

        # trajectory data
        testdir = path.dirname(path.realpath(__file__))
        self._data = pd.read_csv(path.join(testdir, "data", "trajectory.csv"))

    def test_tltk_specification(self) -> None:
        # predicates
        a_matrix = np.array([[1, 0, 0], [-1, 0, 0]], dtype=np.float64)
        predicates = {
            "a": mtl.Predicate("a", a_matrix, np.array([250, -240], dtype=np.float64)),
            "b": mtl.Predicate(
                "b", a_matrix, np.array([240.1, -240], dtype=np.float64)
            ),
        }

        # create specification with TLTK backend
        specification = Specification(self._tltk_formula, predicates, Subsystem.TLTK)

        # filter data
        timestamps = self._data["t"].to_numpy(dtype=np.float32)
        trajectory = self._data[["x1", "x2", "x3"]].to_numpy()
        traces = {"a": trajectory, "b": trajectory}

        # calculate robustness
        robustness = specification.evaluate(traces, timestamps)

        # assert equivalence
        self.assertAlmostEqual(robustness, self._expected_robustness)

    def test_rtamt_discrete_specification(self) -> None:
        # variables
        predicates = {"x1": "float"}

        # create specification with RTAMT (discrete) backend
        specification = Specification(
            self._rtamt_formula, predicates, Subsystem.RTAMT_DISCRETE
        )

        # filter data
        # RTAMT does not support mult-dimensional variable matrices
        timestamps = self._data["t"].to_numpy(dtype=np.float64)
        traces = {"x1": self._data["x1"].to_numpy(dtype=np.float64)}

        # calculate robustness
        robustness = specification.evaluate(traces, timestamps)

        # assert equivalence
        self.assertAlmostEqual(robustness, self._expected_robustness)

from os import path
from typing import TYPE_CHECKING, List
from unittest import TestCase, skipIf

import numpy as np
import pandas as pd

from staliro.specifications import (
    TLTK,
    AdjacencyList,
    GuardMap,
    RTAMTDense,
    RTAMTDiscrete,
    TPTaliro,
)

try:
    import tltk_mtl  # noqa: F401
except ImportError:
    _can_parse = False
else:
    _can_parse = True

try:
    import taliro  # noqa: F401
except ImportError:
    _has_taliro = False
else:
    _has_taliro = True

if _has_taliro and TYPE_CHECKING:
    from taliro.tptaliro import TaliroPredicate

SIG_FIGS = 3


class SpecificationTestCase(TestCase):
    def setUp(self) -> None:
        # The requirements are the same; however, they defer in the syntax since TLTK currently
        # uses the older parsing method of passing predicate names rather than expressions.
        self._requirement = "(not ((always[0.0, 4.0]((x1 <= 250.0) and (x1 >= 240.0))) and (eventually[3.5,4.0]((x1 <= 240.1) and (x1 >= 240.0)))))"
        self._expected_robustness = -0.0160623609618824

        # trajectory data
        testdir = path.dirname(path.realpath(__file__))
        self._data = pd.read_csv(path.join(testdir, "data", "trajectory.csv"))

    @skipIf(
        _can_parse is False,
        "TLTK specification test is not available without parsing functionality",
    )
    def test_tltk_specification(self) -> None:
        predicates = {"x1": 0}
        specification = TLTK(self._requirement, predicates)

        timestamps = self._data["t"].to_numpy(dtype=np.float32).tolist()
        trajectories = self._data[["x1"]].to_numpy().tolist()
        robustness = specification.evaluate(np.atleast_2d(trajectories).T, timestamps)

        self.assertAlmostEqual(robustness, self._expected_robustness, SIG_FIGS)

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

    @skipIf(
        not _has_taliro,
        "Py-TaLiRo library must be installed to run TP-TaLiRo specification euclidean test",
    )
    def test_tp_taliro_specification_euclidean(self) -> None:
        requirement = "(not ((always[0.0, 4.0]((x1_1) and (x1_2))) and (eventually[3.5,4.0]((x1_3) and (x1_4)))))"
        predicates: List[TaliroPredicate] = [
            {
                "name": "x1_1",
                "a": np.array(1.0),
                "b": np.array(250.0),
            },
            {
                "name": "x1_2",
                "a": np.array(-1.0),
                "b": np.array(-240.0),
            },
            {
                "name": "x1_3",
                "a": np.array(1.0),
                "b": np.array(240.1),
            },
            {
                "name": "x1_4",
                "a": np.array(-1.0),
                "b": np.array(-240.0),
            },
        ]
        specification = TPTaliro(requirement, predicates)

        timestamps = self._data["t"].to_numpy(dtype=np.float64).tolist()
        trajectories = self._data["x1"].to_numpy(dtype=np.float32).tolist()
        robustness = specification.evaluate(trajectories, timestamps)

        self.assertAlmostEqual(robustness, self._expected_robustness, SIG_FIGS)

    @skipIf(
        not _has_taliro,
        "Py-TaLiRo library must be installed to run TP-TaLiRo specification hybrid test",
    )
    def test_tp_taliro_specification_hybrid(self) -> None:
        requirement = "globally (p1 and p2)"
        predicates: List[TaliroPredicate] = [
            {"name": "p1", "a": -1.0, "b": 0.0, "l": 1},
            {"name": "p2", "a": -1.0, "b": -5.0, "l": 1},
            {"name": "p3", "a": 1.0, "b": 30.0, "l": 2},
        ]

        graph: AdjacencyList = {"1": ["2"], "2": ["3", "4"], "3": ["1"], "4": ["3"]}

        guards: GuardMap = {
            ("1", "2"): {"a": 1.0, "b": 2.0},
            ("2", "3"): {"a": 1.0, "b": 1.0},
            ("2", "4"): {"a": -1.0, "b": -3.0},
            ("4", "3"): {"a": -1.0, "b": -4.0},
            ("3", "1"): {"a": -1.0, "b": 0.0},
        }
        specification = TPTaliro(requirement, predicates)

        timestamps = self._data["t"].to_numpy(dtype=np.float64)
        trajectories = self._data["x1"].to_numpy(dtype=np.float32)
        locations = self._data["loc"].to_numpy(dtype=np.float32)

        robustness = specification.hybrid(trajectories, timestamps, locations, graph, guards)

        self.assertAlmostEqual(robustness["ds"], -248.4178466796875, SIG_FIGS)
        self.assertEqual(robustness["dl"], -2)

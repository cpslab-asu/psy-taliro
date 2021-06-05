from unittest import TestCase

import numpy as np
import tltk_mtl as mtl

from staliro.specification import Predicate


class ParserTestCase(TestCase):
    def setUp(self) -> None:
        self._preds = {
            "pred1": mtl.Predicate("pred1", np.array([1]), np.array([2])),
            "pred2": mtl.Predicate("pred2", np.array([1]), np.array([4])),
            "pred3": mtl.Predicate("pred3", np.array([1]), np.array([8])),
            "pred4": mtl.Predicate("pred4", np.array([1]), np.array([1])),
            "pred5": mtl.Predicate("pred5", np.array([1]), np.array([-1])),
            "pred6": mtl.Predicate("pred6", np.array([-1]), np.array([1])),
            "pred7": mtl.Predicate("pred7", np.array([-1]), np.array([-1])),
        }

        self._vars = {
            "pred1": Predicate(0),
            "pred2": Predicate(0),
            "pred3": Predicate(0),
            "pred4": Predicate(0),
            "pred5": Predicate(0),
            "pred6": Predicate(0),
            "pred7": Predicate(0),
        }

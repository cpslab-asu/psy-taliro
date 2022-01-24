from unittest import SkipTest, TestCase

import numpy as np


class ParserTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import tltk_mtl as mtl
        except ImportError:
            raise SkipTest("TLTK library is unavailable")

        cls._preds = {
            "pred1": mtl.Predicate("pred1", np.array([1]), np.array([2])),
            "pred2": mtl.Predicate("pred2", np.array([1]), np.array([4])),
            "pred3": mtl.Predicate("pred3", np.array([1]), np.array([8])),
            "pred4": mtl.Predicate("pred4", np.array([1]), np.array([1])),
            "pred5": mtl.Predicate("pred5", np.array([1]), np.array([-1])),
            "pred6": mtl.Predicate("pred6", np.array([-1]), np.array([1])),
            "pred7": mtl.Predicate("pred7", np.array([-1]), np.array([-1])),
            "pred8": mtl.Predicate("pred8", np.array([1]), np.array([110000])),
            "pred9": mtl.Predicate("pred9", np.array([1]), np.array([0.0000112])),
        }

        cls._vars = [
            "pred1",
            "pred2",
            "pred3",
            "pred4",
            "pred5",
            "pred6",
            "pred7",
            "pred8",
            "pred9",
        ]

import tltk_mtl as mtl
from staliro.parser import parse

from ._parser import ParserTestCase


class ImpliesTestCase(ParserTestCase):
    def test_implication(self) -> None:
        self.assertIsInstance(parse(r"pred1 -> pred1", self._preds), mtl.Or)

    def test_implication_with_and(self) -> None:
        self.assertIsInstance(parse(r"(pred1 && pred2) -> pred1", self._preds), mtl.Or)

    def test_chained_implication(self) -> None:
        self.assertIsInstance(parse(r"pred1 -> pred2 -> pred3", self._preds), mtl.Or)

    def test_implication_with_multi_and(self) -> None:
        self.assertIsInstance(parse(r"pred1 -> (pred1 && pred2 && pred3)", self._preds), mtl.Or)

    def test_implication_with_or_and_literal(self) -> None:
        self.assertIsInstance(
            parse(r"pred1 -> pred2 -> (pred1 || pred2) -> pred3", self._preds), mtl.Or
        )

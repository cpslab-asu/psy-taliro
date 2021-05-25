import tltk_mtl as mtl
from staliro.parser import parse

from ._parser import ParserTestCase


class NegationTestCase(ParserTestCase):
    def test_negation(self) -> None:
        self.assertIsInstance(parse("!pred1", self._preds), mtl.Not)
        self.assertIsInstance(parse("!pred3", self._preds), mtl.Not)

    def test_double_negation(self) -> None:
        self.assertIsInstance(parse("!!(pred2)", self._preds), mtl.Not)

    def test_negation_with_and(self) -> None:
        self.assertIsInstance(parse("!(pred1 and pred2)", self._preds), mtl.Not)

    def test_many_negation_with_and(self) -> None:
        self.assertIsInstance(
            parse("!!!!!(pred1 and pred2 and pred3)", self._preds), mtl.Not
        )

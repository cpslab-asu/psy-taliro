import tltk_mtl as mtl
from staliro.parser import parse

from ._parser import ParserTestCase


class AndTestCase(ParserTestCase):
    def test_logical_and(self) -> None:
        self.assertIsInstance(parse("pred1 && pred2", self._preds), mtl.And)

    def test_logical_and_alternate_syntax(self) -> None:
        self.assertIsInstance(
            parse("pred1 & pred1 && pred1 /\ pred1 and pred1", self._preds), mtl.And
        )

    def test_logical_and_with_negation(self) -> None:
        self.assertIsInstance(parse("pred1 && !pred2 && pred3", self._preds), mtl.And)

    def test_logical_and_with_or(self) -> None:
        self.assertIsInstance(parse("pred1 || pred2 && pred3", self._preds), mtl.And)

    def logical_and_with_or_alternate_syntax(self) -> None:
        self.assertIsInstance(
            parse("pred2 | pred3 && pred2 | pred2 && pred1", self._preds), mtl.And
        )

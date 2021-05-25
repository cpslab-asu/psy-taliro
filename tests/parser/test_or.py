import tltk_mtl as mtl
from staliro.parser import parse

from ._parser import ParserTestCase


class OrTestCase(ParserTestCase):
    def test_or(self) -> None:
        self.assertIsInstance(parse("pred1 || pred1", self._preds), mtl.Or)

    def test_or_alternate_syntax(self) -> None:
        self.assertIsInstance(
            parse("pred1 | pred1 || pred1 \/ pred1 or pred1", self._preds), mtl.Or
        )

    def test_or_with_negation(self) -> None:
        self.assertIsInstance(parse("pred1 or !pred2 || pred3", self._preds), mtl.Or)

    def test_or_with_and(self) -> None:
        self.assertIsInstance(parse("pred1 and pred2 or pred3", self._preds), mtl.Or)

    def test_or_with_and_alternate_syntax(self) -> None:
        self.assertIsInstance(
            parse("pred2 and pred3 & pred2 and pred2 or pred1", self._preds), mtl.Or
        )

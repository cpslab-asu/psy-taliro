import tltk_mtl as mtl
from staliro.parser import parse

from ._parser import ParserTestCase


class FinallyTestCase(ParserTestCase):
    def test_finally_infinite(self) -> None:
        self.assertIsInstance(parse("<>(1, inf) pred1", self._preds), mtl.Finally)

    def test_finally_nested(self) -> None:
        self.assertIsInstance(
            parse("<>(1, 100) (finally(1.0, 200) (pred1 && pred2))", self._preds),
            mtl.Finally,
        )

    def test_finally_alternate_syntax(self) -> None:
        self.assertIsInstance(
            parse("<>(1, 100) <>(5, 50) F(25, 35) <>(27, 30) pred1", self._preds),
            mtl.Finally,
        )

    def test_finally_with_and(self) -> None:
        self.assertIsInstance(parse("F(1, 1000) (pred1 && pred2)", self._preds), mtl.Finally)

    def test_finally_with_or(self) -> None:
        self.assertIsInstance(parse("<>(25, 3000) (pred2 | pred3)", self._preds), mtl.Finally)

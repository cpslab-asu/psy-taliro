import tltk_mtl as mtl
from staliro.parser import parse

from ._parser import ParserTestCase


class GloballyTestCase(ParserTestCase):
    def test_globally_infinite(self) -> None:
        self.assertIsInstance(parse("[](1, inf) pred1", self._preds), mtl.Global)

    def test_globally_alternate_syntax_with_and(self) -> None:
        self.assertIsInstance(
            parse("[](1, 100) G(1, 100) globally(1, 100) (pred1 && pred2)", self._preds),
            mtl.Global,
        )

    def test_globally_alternate_syntax(self) -> None:
        self.assertIsInstance(
            parse("[](1, 100) [](5, 50) G(25, 35) [](27, 30) pred1", self._preds),
            mtl.Global,
        )

    def test_globally_with_and(self) -> None:
        self.assertIsInstance(parse("G(1, 1000) (pred1 && pred2)", self._preds), mtl.Global)

    def test_globally_with_or(self) -> None:
        self.assertIsInstance(parse("[](25, 3000) (pred2 | pred3)", self._preds), mtl.Global)

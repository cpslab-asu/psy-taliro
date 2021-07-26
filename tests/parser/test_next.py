import tltk_mtl as mtl
from staliro.parser import parse

from ._parser import ParserTestCase


class NextTestCase(ParserTestCase):
    def test_next(self) -> None:
        self.assertIsInstance(parse(r"next pred1", self._preds), mtl.Next)

    def test_next_alternate_synax(self) -> None:
        self.assertIsInstance(parse(r"next X pred1", self._preds), mtl.Next)

    def test_next_with_and(self) -> None:
        self.assertIsInstance(parse(r"next (pred1 && pred2)", self._preds), mtl.Next)

    def test_nested_next_with_and(self) -> None:
        self.assertIsInstance(parse(r"X (pred1 && X X X pred3)", self._preds), mtl.Next)

    def test_many_next(self) -> None:
        self.assertIsInstance(parse(r"X X X X X X X X (pred1 & pred2)", self._preds), mtl.Next)

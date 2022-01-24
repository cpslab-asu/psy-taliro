from unittest import skipIf

try:
    from staliro.parser import parse
except:
    _can_parse = False
else:
    _can_parse = True

from ._parser import ParserTestCase


@skipIf(
    _can_parse is False, "Implies parsing test case is not available without parsing functionality"
)
class ImpliesTestCase(ParserTestCase):
    def assert_is_or(self, value):
        import tltk_mtl as mtl

        self.assertIsInstance(value, mtl.Or)

    def test_implication(self) -> None:
        self.assert_is_or(parse(r"pred1 -> pred1", self._preds))

    def test_implication_with_and(self) -> None:
        self.assert_is_or(parse(r"(pred1 && pred2) -> pred1", self._preds))

    def test_chained_implication(self) -> None:
        self.assert_is_or(parse(r"pred1 -> pred2 -> pred3", self._preds))

    def test_implication_with_multi_and(self) -> None:
        self.assert_is_or(parse(r"pred1 -> (pred1 && pred2 && pred3)", self._preds))

    def test_implication_with_or_and_literal(self) -> None:
        self.assert_is_or(parse(r"pred1 -> pred2 -> (pred1 || pred2) -> pred3", self._preds))

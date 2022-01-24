from unittest import skipIf

try:
    from staliro.parser import parse
except:
    _can_parse = False
else:
    _can_parse = True

from ._parser import ParserTestCase


@skipIf(
    _can_parse is False, "Negation parsing test case is not available without parsing functionality"
)
class NegationTestCase(ParserTestCase):
    def assert_is_not(self, value):
        import tltk_mtl as mtl

        self.assertIsInstance(value, mtl.Not)

    def test_negation(self) -> None:
        self.assert_is_not(parse(r"!pred1", self._preds))
        self.assert_is_not(parse(r"!pred3", self._preds))

    def test_double_negation(self) -> None:
        self.assert_is_not(parse(r"!!(pred2)", self._preds))

    def test_negation_with_and(self) -> None:
        self.assert_is_not(parse(r"!(pred1 and pred2)", self._preds))

    def test_many_negation_with_and(self) -> None:
        self.assert_is_not(parse(r"!!!!!(pred1 and pred2 and pred3)", self._preds))

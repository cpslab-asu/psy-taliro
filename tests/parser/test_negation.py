from unittest import skipIf

try:
    from staliro.parser import parse
except:
    _can_parse = False
else:
    _can_parse = True

from ._parser import ParserTestCase


@skipIf(_can_parse is False, "Negation parsing test case is not available without parsing functionality")
class NegationTestCase(ParserTestCase):
    def assertIsNot_(self, value):
        import tltk_mtl as mtl

        self.assertIsInstance(value, mtl.Not)

    def test_negation(self) -> None:
        self.assertIsNot_(parse(r"!pred1", self._preds))
        self.assertIsNot_(parse(r"!pred3", self._preds))

    def test_double_negation(self) -> None:
        self.assertIsNot_(parse(r"!!(pred2)", self._preds))

    def test_negation_with_and(self) -> None:
        self.assertIsNot_(parse(r"!(pred1 and pred2)", self._preds))

    def test_many_negation_with_and(self) -> None:
        self.assertIsNot_(parse(r"!!!!!(pred1 and pred2 and pred3)", self._preds))

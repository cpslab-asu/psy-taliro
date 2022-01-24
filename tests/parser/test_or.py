from unittest import skipIf

try:
    from staliro.parser import parse
except:
    _can_parse = False
else:
    _can_parse = True

from ._parser import ParserTestCase


@skipIf(_can_parse is False, "Or parsing test case is not available without parsing functionality")
class OrTestCase(ParserTestCase):
    def assert_is_or(self, value):
        import tltk_mtl as mtl

        self.assertIsInstance(value, mtl.Or)

    def test_or(self) -> None:
        self.assert_is_or(parse(r"pred1 || pred1", self._preds))

    def test_or_alternate_syntax(self) -> None:
        self.assert_is_or(parse(r"pred1 | pred1 || pred1 \/ pred1 or pred1", self._preds))

    def test_or_with_negation(self) -> None:
        self.assert_is_or(parse(r"pred1 or !pred2 || pred3", self._preds))

    def test_or_with_and(self) -> None:
        self.assert_is_or(parse(r"pred1 and pred2 or pred3", self._preds))

    def test_or_with_and_alternate_syntax(self) -> None:
        self.assert_is_or(parse(r"pred2 and pred3 & pred2 and pred2 or pred1", self._preds))

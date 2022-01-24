from unittest import skipIf

try:
    from staliro.parser import parse
except:
    _can_parse = False
else:
    _can_parse = True

from ._parser import ParserTestCase


@skipIf(
    _can_parse is False, "Global parsing test case is not available without parsing functionality"
)
class GloballyTestCase(ParserTestCase):
    def assert_is_global(self, value):
        import tltk_mtl as mtl

        self.assertIsInstance(value, mtl.Global)

    def test_globally_infinite(self) -> None:
        self.assert_is_global(parse(r"[](1, inf) pred1", self._preds))

    def test_globally_alternate_syntax_with_and(self) -> None:
        self.assert_is_global(
            parse(r"[](1, 100) G(1, 100) globally(1, 100) (pred1 && pred2)", self._preds)
        )

    def test_globally_alternate_syntax(self) -> None:
        self.assert_is_global(
            parse(r"[](1, 100) [](5, 50) G(25, 35) [](27, 30) pred1", self._preds)
        )

    def test_globally_with_and(self) -> None:
        self.assert_is_global(parse(r"G(1, 1000) (pred1 && pred2)", self._preds))

    def test_globally_with_or(self) -> None:
        self.assert_is_global(parse(r"[](25, 3000) (pred2 | pred3)", self._preds))

from unittest import skipIf

try:
    from staliro.parser import parse
except:
    _can_parse = False
else:
    _can_parse = True

from ._parser import ParserTestCase


@skipIf(
    _can_parse is False, "Finally parsing test case is not available without parsing functionality"
)
class FinallyTestCase(ParserTestCase):
    def assertIsFinally(self, value):
        import tltk_mtl as mtl

        self.assertIsInstance(value, mtl.Finally)

    def test_finally_infinite(self) -> None:
        self.assertIsFinally(parse(r"<>(1, inf) pred1", self._preds))

    def test_finally_nested(self) -> None:
        self.assertIsFinally(
            parse(r"<>(1, 100) (finally(1.0, 200) (pred1 && pred2))", self._preds)
        )

    def test_finally_alternate_syntax(self) -> None:
        self.assertIsFinally(
            parse(r"<>(1, 100) <>(5, 50) F(25, 35) <>(27, 30) pred1", self._preds)
        )

    def test_finally_with_and(self) -> None:
        self.assertIsFinally(parse(r"F(1, 1000) (pred1 && pred2)", self._preds))

    def test_finally_with_or(self) -> None:
        self.assertIsFinally(self._parser.parse(r"<>(25, 3000) (pred2 | pred3)", self._preds))

from unittest import skipIf

try:
    from staliro.parser import parse
except:
    _can_parse = False
else:
    _can_parse = True

from ._parser import ParserTestCase


@skipIf(
    _can_parse is False,
    "Predicate parsing test case is not available without parsing functionality",
)
class PredicateTestCase(ParserTestCase):
    def _do_test(self, phi: str, expected) -> None:
        import tltk_mtl as mtl

        predicate = parse(phi, self._vars)

        assert isinstance(predicate, mtl.Predicate)

        self.assertEqual(predicate.variable_name, expected.variable_name)
        self.assertEqual(predicate.A_Matrix, expected.A_Matrix)
        self.assertEqual(predicate.bound, expected.bound)

    def test_predicate_pos_ns_less_than_pos(self) -> None:
        self._do_test(r"pred4 <= 1.0", self._preds["pred4"])

    def test_predicate_pos_ns_less_than_neg(self) -> None:
        self._do_test(r"pred5 <= -1.0", self._preds["pred5"])

    def test_predicate_neg_ns_less_than_pos(self) -> None:
        self._do_test(r"-pred6 <= 1.0", self._preds["pred6"])

    def test_predicate_neg_ns_less_than_neg(self) -> None:
        self._do_test(r"-pred7 <= -1.0", self._preds["pred7"])

    def test_predicate_pos_ns_greater_than_pos(self) -> None:
        self._do_test(r"pred7 >= 1.0", self._preds["pred7"])

    def test_predicate_pos_ns_greater_than_neg(self) -> None:
        self._do_test(r"pred6 >= -1.0", self._preds["pred6"])

    def test_predicate_neg_ns_greater_than_pos(self) -> None:
        self._do_test(r"-pred5 >= 1.0", self._preds["pred5"])

    def test_predicate_neg_ns_greater_than_neg(self) -> None:
        self._do_test(r"-pred4 >= -1.0", self._preds["pred4"])

    def test_predicate_pos_ns_less_than_pos_scientific_pos(self) -> None:
        self._do_test(r"pred8 <= 1.1e5", self._preds["pred8"])

    def test_predicate_pos_ns_less_than_pos_scientific_neg(self) -> None:
        self._do_test(r"pred9 <= 1.12e-5", self._preds["pred9"])

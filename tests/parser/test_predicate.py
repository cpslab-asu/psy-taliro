from staliro.parser import parse

from ._parser import ParserTestCase


class PredicateTestCase(ParserTestCase):
    def test_predicate_positive_ns_less_than_positive_name(self) -> None:
        self.assertEqual(
            parse("pred4 <= 1.0", self._vars).variable_name,
            self._preds["pred4"].variable_name,
        )

    def test_predicate_positive_ns_less_than_positive_matrix(self) -> None:
        self.assertEqual(parse("pred4 <= 1.0", self._vars).A_Matrix, self._preds["pred4"].A_Matrix)

    def test_predicate_positive_ns_less_than_positive_bound(self) -> None:
        self.assertEqual(parse("pred4 <= 1.0", self._vars).bound, self._preds["pred4"].bound)

    def test_predicate_positive_ns_less_than_negative_name(self) -> None:
        self.assertEqual(
            parse("pred5 <= -1.0", self._vars).variable_name,
            self._preds["pred5"].variable_name,
        )

    def test_predicate_positive_ns_less_than_negative_matrix(self) -> None:
        self.assertEqual(parse("pred5 <= -1.0", self._vars).A_Matrix, self._preds["pred5"].A_Matrix)

    def test_predicate_positive_ns_less_than_negative_bound(self) -> None:
        self.assertEqual(parse("pred5 <= -1.0", self._vars).bound, self._preds["pred5"].bound)

    def test_predicate_negative_ns_less_than_positive_name(self) -> None:
        self.assertEqual(
            parse("-pred6 <= 1.0", self._vars).variable_name,
            self._preds["pred6"].variable_name,
        )

    def test_predicate_negative_ns_less_than_positive_matrix(self) -> None:
        self.assertEqual(parse("-pred6 <= 1.0", self._vars).A_Matrix, self._preds["pred6"].A_Matrix)

    def test_predicate_negative_ns_less_than_positive_bound(self) -> None:
        self.assertEqual(parse("-pred6 <= 1.0", self._vars).bound, self._preds["pred6"].bound)

    def test_predicate_negative_ns_less_than_negative_name(self) -> None:
        self.assertEqual(
            parse("-pred6 <= -1.0", self._vars).variable_name,
            self._preds["pred6"].variable_name,
        )

    def test_predicate_negative_ns_less_than_negative_matrix(self) -> None:
        self.assertEqual(
            parse("-pred7 <= -1.0", self._vars).A_Matrix,
            self._preds["pred7"].A_Matrix,
        )

    def test_predicate_negative_ns_less_than_negative_bound(self) -> None:
        self.assertEqual(parse("-pred7 <= -1.0", self._vars).bound, self._preds["pred7"].bound)

    def test_predicate_positive_ns_greater_than_positive_name(self) -> None:
        self.assertEqual(
            parse("pred7 >= 1.0", self._vars).variable_name,
            self._preds["pred7"].variable_name,
        )

    def test_predicate_positive_ns_greater_than_positive_matrix(self) -> None:
        self.assertEqual(parse("pred7 >= 1.0", self._vars).A_Matrix, self._preds["pred7"].A_Matrix)

    def test_predicate_positive_ns_greater_than_positive_bound(self) -> None:
        self.assertEqual(parse("pred7 >= 1.0", self._vars).bound, self._preds["pred7"].bound)

    def test_predicate_positive_ns_greater_than_negative_name(self) -> None:
        self.assertEqual(
            parse("pred6 >= -1.0", self._vars).variable_name,
            self._preds["pred6"].variable_name,
        )

    def test_predicate_positive_ns_greater_than_negative_matrix(self) -> None:
        self.assertEqual(parse("pred6 >= -1.0", self._vars).A_Matrix, self._preds["pred6"].A_Matrix)

    def test_predicate_positive_ns_greater_than_negative_bound(self) -> None:
        self.assertEqual(parse("pred6 >= -1.0", self._vars).bound, self._preds["pred6"].bound)

    def test_predicate_negative_ns_greater_than_positive_name(self) -> None:
        self.assertEqual(
            parse("-pred5 >= 1.0", self._vars).variable_name,
            self._preds["pred5"].variable_name,
        )

    def test_predicate_negative_ns_greater_than_positive_matrix(self) -> None:
        self.assertEqual(parse("-pred5 >= 1.0", self._vars).A_Matrix, self._preds["pred5"].A_Matrix)

    def test_predicate_negative_ns_greater_than_positive_bound(self) -> None:
        self.assertEqual(parse("-pred5 >= 1.0", self._vars).bound, self._preds["pred5"].bound)

    def test_predicate_negative_ns_greater_than_negative_name(self) -> None:
        self.assertEqual(
            parse("-pred4 >= -1.0", self._vars).variable_name,
            self._preds["pred4"].variable_name,
        )

    def test_predicate_negative_ns_greater_than_negative_matrix(self) -> None:
        self.assertEqual(
            parse("-pred4 >= -1.0", self._vars).A_Matrix,
            self._preds["pred4"].A_Matrix,
        )

    def test_predicate_negative_ns_greater_than_negative_bound(self) -> None:
        self.assertEqual(parse("-pred4 >= -1.0", self._vars).bound, self._preds["pred4"].bound)

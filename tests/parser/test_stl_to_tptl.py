from unittest import TestCase

from staliro.parser import translate
from staliro.parser import TemporalLogic as TL


class StlTptlTranslationTestCase(TestCase):
    """Test the equivalency translations from STL to TPTL."""

    def setUp(self) -> None:
        """Prepare reusable items."""

        pass

    def test_translate_stl_to_stl(self) -> None:
        source = r"always[0, 10] (a and b)"
        translation = translate(source, TL.STL, TL.STL)

        self.assertEqual(source, translation)

    def test_translate_tptl_to_tptl(self) -> None:
        source = r"@Var_t [](({ Var_t >= 0 } /\ { Var_t <= 10 }) -> (a /\ b))"
        translation = translate(source, TL.TPTL, TL.TPTL)

        self.assertEqual(source, translation)

    def test_translate_negation(self) -> None:
        source = r"not not not a"
        translation = translate(source, TL.STL, TL.TPTL)

        self.assertEqual("! ! ! a", translation)

    def test_translate_next(self) -> None:
        pass

    def test_translate_eventually(self) -> None:
        pass

    def test_translate_always(self) -> None:
        pass

    def test_translate_until(self) -> None:
        pass

    def test_translate_release(self) -> None:
        pass

    def test_translate_implication(self) -> None:
        pass

    def test_translate_equivalence(self) -> None:
        pass

    def test_translate_conjunction(self) -> None:
        pass

    def test_translate_disjunction(self) -> None:
        pass

    def test_translate_unbounded_predicate(self) -> None:
        pass

    def test_translate_bounded_predicate(self) -> None:
        pass

    def test_translate_complex_requirement_01(self) -> None:
        pass

    def test_translate_complex_requirement_01(self) -> None:
        pass

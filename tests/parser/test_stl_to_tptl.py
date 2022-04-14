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
        source = r"next a"
        translation = translate(source, TL.STL, TL.TPTL)

        self.assertEqual("X a", translation)

    def test_translate_eventually(self) -> None:
        source = r"eventually a"
        translation = translate(source, TL.STL, TL.TPTL)

        self.assertEqual("<> a", translation)

    def test_translate_always(self) -> None:
        source = r"always a"
        translation = translate(source, TL.STL, TL.TPTL)

        self.assertEqual("[] a", translation)

    def test_translate_until(self) -> None:
        source = r"a until b"
        translation = translate(source, TL.STL, TL.TPTL)

        self.assertEqual("a U b", translation)

    def test_translate_release(self) -> None:
        source = r"a release b"
        translation = translate(source, TL.STL, TL.TPTL)

        self.assertEqual("a R b", translation)

    def test_translate_implication(self) -> None:
        source = r"a implies (next b)"
        translation = translate(source, TL.STL, TL.TPTL)

        self.assertEqual("a -> ( X b )", translation)

    def test_translate_equivalence(self) -> None:
        source = r"a iff (always b)"
        translation = translate(source, TL.STL, TL.TPTL)

        self.assertEqual("a <-> ( [] b )", translation)

    def test_translate_conjunction(self) -> None:
        source = r"a and b and c"
        translation = translate(source, TL.STL, TL.TPTL)

        self.assertEqual("a /\ b /\ c", translation)

    def test_translate_disjunction(self) -> None:
        source = r"a or b or c"
        translation = translate(source, TL.STL, TL.TPTL)

        self.assertEqual("a \/ b \/ c", translation)

    def test_translate_unbounded_predicate(self) -> None:
        source = r"globally (eventually a) /\ (eventually b)"
        translation = translate(source, TL.STL, TL.TPTL)

        self.assertEqual("[] ( <> a ) /\ ( <> b )", translation)

    # def test_translate_bounded_predicate(self) -> None:
    #     source = r"always[0, 10] (a /\ (eventually[0, 3] b))"
    #     translation = translate(source, TL.STL, TL.TPTL)

    #     self.assertEqual("@Var_t1 (({ Var_t1 >= 0 } /\ { Var_t1 <= 10}) -> (a /\ (@Var_t2 <>(({ Var_t2 >= 0 } /\ { Var_t2 <= 3 }) /\ b))))", translation)

    # def test_translate_complex_requirement_01(self) -> None:
    #     pass

    # def test_translate_complex_requirement_02(self) -> None:
    #     pass

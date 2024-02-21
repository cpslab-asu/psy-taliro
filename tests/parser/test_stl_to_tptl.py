from unittest import TestCase, skipIf

try:
    from staliro.parser import TemporalLogic, translate
except ImportError:
    _can_parse = False
else:
    _can_parse = True


@skipIf(_can_parse is False, "Translation test case is not available without parsing functionality")
class StlTptlTranslationTestCase(TestCase):
    """Test the equivalency translations from STL to TPTL."""

    def setUp(self) -> None:
        """Prepare reusable items."""

        pass

    def test_translate_stl_to_stl(self) -> None:
        source = r"always[0, 10] (a and b)"
        translation = translate(source, TemporalLogic.STL, TemporalLogic.STL)

        self.assertEqual(source, translation)

    def test_translate_tptl_to_tptl(self) -> None:
        source = r"@Var_t [](({ Var_t >= 0 } /\ { Var_t <= 10 }) -> (a /\ b))"
        translation = translate(source, TemporalLogic.TPTL, TemporalLogic.TPTL)

        self.assertEqual(source, translation)

    def test_translate_negation(self) -> None:
        source = r"not not not a"
        translation = translate(source, TemporalLogic.STL, TemporalLogic.TPTL)

        self.assertEqual("! ! ! a", translation)

    def test_translate_next(self) -> None:
        source = r"next a"
        translation = translate(source, TemporalLogic.STL, TemporalLogic.TPTL)

        self.assertEqual("X a", translation)

    def test_translate_eventually(self) -> None:
        source = r"eventually a"
        translation = translate(source, TemporalLogic.STL, TemporalLogic.TPTL)

        self.assertEqual("<> a", translation)

    def test_translate_always(self) -> None:
        source = r"always a"
        translation = translate(source, TemporalLogic.STL, TemporalLogic.TPTL)

        self.assertEqual("[] a", translation)

    def test_translate_until(self) -> None:
        source = r"a until b"
        translation = translate(source, TemporalLogic.STL, TemporalLogic.TPTL)

        self.assertEqual("a U b", translation)

    def test_translate_release(self) -> None:
        source = r"a release b"
        translation = translate(source, TemporalLogic.STL, TemporalLogic.TPTL)

        self.assertEqual("a R b", translation)

    def test_translate_implication(self) -> None:
        source = r"a implies (next b)"
        translation = translate(source, TemporalLogic.STL, TemporalLogic.TPTL)

        self.assertEqual("a -> ( X b )", translation)

    def test_translate_equivalence(self) -> None:
        source = r"a iff (always b)"
        translation = translate(source, TemporalLogic.STL, TemporalLogic.TPTL)

        self.assertEqual("a <-> ( [] b )", translation)

    def test_translate_conjunction(self) -> None:
        source = r"a and b and c"
        translation = translate(source, TemporalLogic.STL, TemporalLogic.TPTL)

        self.assertEqual(r"a /\ b /\ c", translation)

    def test_translate_disjunction(self) -> None:
        source = r"a or b or c"
        translation = translate(source, TemporalLogic.STL, TemporalLogic.TPTL)

        self.assertEqual(r"a \/ b \/ c", translation)

    def test_translate_bounded_next(self) -> None:
        source = r"next[0, 10] a"
        translation = translate(source, TemporalLogic.STL, TemporalLogic.TPTL)

        self.assertEqual(r"@Var_t0 X(({ Var_t0 >= 0.0 } /\ { Var_t0 <= 10.0 }) /\ a)", translation)

    def test_translate_bounded_eventually(self) -> None:
        source = r"eventually[3, 5] a"
        translation = translate(source, TemporalLogic.STL, TemporalLogic.TPTL)

        self.assertEqual(r"@Var_t0 <>(({ Var_t0 >= 3.0 } /\ { Var_t0 <= 5.0 }) /\ a)", translation)

    def test_translate_bounded_always(self) -> None:
        source = r"always[0, 100] a"
        translation = translate(source, TemporalLogic.STL, TemporalLogic.TPTL)

        self.assertEqual(
            r"@Var_t0 [](({ Var_t0 >= 0.0 } /\ { Var_t0 <= 100.0 }) -> a)", translation
        )

    def test_translate_bounded_until(self) -> None:
        source = r"a until[0, 2] b"
        translation = translate(source, TemporalLogic.STL, TemporalLogic.TPTL)

        self.assertEqual(
            r"@Var_t0 ( a U (({ Var_t0 >= 0.0 } /\ { Var_t0 <= 2.0 }) /\ b))", translation
        )

    def test_translate_bounded_release(self) -> None:
        source = r"a release[0, 5] b"
        translation = translate(source, TemporalLogic.STL, TemporalLogic.TPTL)

        self.assertEqual(
            r"!(@Var_t0 (!a U (({ Var_t0 >= 0.0 } /\ { Var_t0 <= 5.0 }) /\ !b)))", translation
        )

    def test_translate_predicate(self) -> None:
        source = r"globally (eventually a) /\ (eventually b)"
        translation = translate(source, TemporalLogic.STL, TemporalLogic.TPTL)

        self.assertEqual(r"[] ( <> a ) /\ ( <> b )", translation)

    def test_translate_bounded_predicate(self) -> None:
        source = r"always[0, 10] (a /\ (eventually[0, 3] b))"
        translation = translate(source, TemporalLogic.STL, TemporalLogic.TPTL)

        self.assertEqual(
            r"@Var_t0 [](({ Var_t0 >= 0.0 } /\ { Var_t0 <= 10.0 }) -> ( a /\ ( @Var_t1 <>(({ Var_t1 >= 0.0 } /\ { Var_t1 <= 3.0 }) /\ b) ) ))",
            translation,
        )

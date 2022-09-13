from __future__ import annotations

from enum import IntEnum, auto
from typing import Any, Dict, Optional, Sequence, Union

import tltk_mtl as mtl
from antlr4.CommonTokenStream import CommonTokenStream
from antlr4.InputStream import InputStream

from .stlLexer import stlLexer as Lexer
from .stlParser import stlParser as Parser
from .stlParserVisitor import stlParserVisitor as Visitor

PredicateNameSeq = Sequence[str]
PredicateDict = Dict[str, mtl.Predicate]
Predicates = Union[PredicateNameSeq, PredicateDict]
TltkObject = Union[
    mtl.And,
    mtl.Finally,
    mtl.Global,
    mtl.Implication,
    mtl.Next,
    mtl.Not,
    mtl.Or,
    mtl.Predicate,
    mtl.Until,
]


class TemporalLogic(IntEnum):
    """Currently supported Temporal Logic (TL) specifications.

    Attributes:
       STL: Signal Temporal Logic
       TPTL: Timed Propositional Temporal Logic
    """

    STL = auto()
    TPTL = auto()

    def __lt__(self, other: int) -> Any:
        if not isinstance(other, TemporalLogic):
            return NotImplemented

        return self.value < other.value

    def __str__(self) -> str:
        return self.name


def parse(formula: str, predicates: Predicates, mode: str = "cpu") -> Optional[TltkObject]:
    """TLTk parser parses a specification requirement into an equivalent TLTk structure

    Attributes:
        formula: The formal specification requirement
        predicates: The set of Predicate(s) used in the requirement
        mode: The TLTk computation mode
    """
    input_stream = InputStream(formula)

    lexer = Lexer(input_stream)
    stream = CommonTokenStream(lexer)

    parser = Parser(stream)
    tree = parser.stlSpecification()
    visitor = Visitor(lexer, predicates, mode)

    return visitor.visit(tree)  # type: ignore


class SpecificationSyntaxError(Exception):
    """Exception to represent a syntax error in a specification."""

    pass


def _stl_to_tptl(stream: InputStream) -> str:
    """Translate STL to TPTL.

    Arguments:
        stream: ANTLR input stream.

    Returns:
        An equivalently translated formula.
    """

    from .stlLexer import stlLexer as Lexer
    from .stlParser import stlParser as Parser
    from .stlTptlParserVisitorTranslator import stlTptlParserVisitorTranslator as TptlVisitor

    try:
        lexer = Lexer(stream)
        stream = CommonTokenStream(lexer)

        parser = Parser(stream)
        tree = parser.stlSpecification()
        visitor = TptlVisitor(lexer)

        return visitor.visit(tree)  # type: ignore
    except:
        raise SpecificationSyntaxError("STL formula has a syntax error")


class UnsupportedTranslationError(Exception):
    """An exception thrown when an invalid translation scheme is selected."""

    pass


def translate(formula: str, source: TemporalLogic, target: TemporalLogic) -> str:
    """Translate a source TL to a target TL.

    Arguments:
        formula: The source TL specification.
        source: The source Temporal Logic formula to translate from.
        target: The target Temporal Logic formula to translate to.

    Returns:
        An equivalently translated formula.
    """

    stream = InputStream(formula)

    if source == TemporalLogic.STL and target == TemporalLogic.TPTL:
        return _stl_to_tptl(stream)
    elif source == target:
        return formula
    else:
        raise UnsupportedTranslationError(f"cannot translate from {source} to {target}")

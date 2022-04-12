from __future__ import annotations

from enum import Enum
from typing import Dict, Optional, Sequence, Union

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


class TemporalLogic(Enum):
    """Currently supported Temporal Logic (TL) specifications.

    Attributes:
       STL: Signal Temporal Logic
       TPTL: Timed Propositional Temporal Logic
    """

    STL = 1
    TPTL = 2


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


def translate(formula: str, source: TemporalLogic, target: TemporalLogic) -> str:
    """Translate a source TL to a target TL.

    Arguments:
        source: The source Temporal Logic formula to translate from.
        target: The target Temporal Logic formula to translate to.

    Returns:
        An equivalently translated formula.
    """

    if source > target:
        raise UserWarning("translation down to a lower logic is not well defined")

    input_stream = InputStream(formula)

    if source == TemporalLogic.STL and target == TemporalLogic.TPTL:
        from .stlLexer import stlLexer as Lexer
        from .stlParser import stlParser as Parser
        from .stlTptlParserVisitorTranslator import stlTptlParserVisitorTranslator as Visitor

        lexer = Lexer(input_stream)
        stream = CommonTokenStream(lexer)

        parser = Parser(stream)
        tree = parser.stlSpecification()
        visitor = Visitor()

        return visitor.visit(tree)

    elif source == target:
        return source

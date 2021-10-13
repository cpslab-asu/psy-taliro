from __future__ import annotations

from typing import Dict, Optional, Union, Sequence

from antlr4.CommonTokenStream import CommonTokenStream
from antlr4.InputStream import InputStream

try:
    import tltk_mtl as mtl
except ImportError:
    _has_tltk = False
else:
    _has_tltk = True
    PredicateDict = Dict[str, mtl.Predicate]
    Predicates = Union[Sequence[str], PredicateDict]
    StlSpecification = Union[
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


def parse(formula: str, predicates: Predicates, mode: str = "cpu") -> Optional[StlSpecification]:
    """TLTk parser parses a specification requirement into an equivalent TLTk structure

    Attributes:
        formula: The formal specification requirement
        predicates: The set of Predicate(s) used in the requirement
        mode: The TLTk computation mode
    """

    if not _has_tltk:
        raise RuntimeError("TLTK must be installed to use parser functionality")

    from .stlLexer import stlLexer as Lexer
    from .stlParser import stlParser as Parser
    from .stlParserVisitor import stlParserVisitor as Visitor

    input_stream = InputStream(formula)

    lexer = Lexer(input_stream)
    stream = CommonTokenStream(lexer)

    parser = Parser(stream)
    tree = parser.stlSpecification()
    visitor = Visitor(lexer, predicates, mode)

    return visitor.visit(tree)  # type: ignore

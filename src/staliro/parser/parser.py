from __future__ import annotations

from importlib.util import find_spec
from typing import Dict, Optional, TYPE_CHECKING, Union, Sequence

from antlr4.CommonTokenStream import CommonTokenStream
from antlr4.InputStream import InputStream

if TYPE_CHECKING:
    from tltk_mtl import Predicate

    PredicateDict = Dict[str, Predicate]
    Predicates = Union[Sequence[str], PredicateDict]

from .stlSpecification import StlSpecification

def parse(formula: str, predicates: Predicates, mode: str = "cpu") -> Optional[StlSpecification]:
    """TLTk parser parses a specification requirement into an equivalent TLTk structure

    Attributes:
        formula: The formal specification requirement
        predicates: The set of Predicate(s) used in the requirement
        mode: The TLTk computation mode
    """

    if find_spec("tltk_mtl") is None:
        raise RuntimeError("TLTK must be installed to use parser functionality")

    from .stlLexer import stlLexer as Lexer
    from .stlParser import stlParser as Parser
    from .stlParserVisitor import stlParserVisitor as Visitor

    # convert string to ANTLRv4 InputStream
    input_stream = InputStream(formula)

    # create a token stream from the STPL lexer
    lexer = Lexer(input_stream)
    stream = CommonTokenStream(lexer)

    # return a ParseTree from the STPL parser
    parser = Parser(stream)
    tree = parser.stlSpecification()

    # visit the tree and generate equivalent MTL from formula
    visitor = Visitor(lexer, predicates, mode)

    return visitor.visit(tree)  # type: ignore

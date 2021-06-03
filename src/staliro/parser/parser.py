from __future__ import annotations

from importlib.util import find_spec
from typing import Dict, Optional, TYPE_CHECKING

from antlr4.CommonTokenStream import CommonTokenStream
from antlr4.InputStream import InputStream

if TYPE_CHECKING:
    from tltk_mtl import Predicate

    Predicates = Dict[str, Predicate]

from .stlSpecification import StlSpecification


# parse is used to translate a string MTL formula
# into an MTL representation using the TLTk Python module developed
# by Nogthar_ and Bardh Hoxha.
#
# @param formula:    A string representing the formula to be parsed. It
#                    should be noted that predicate names should correspond
#                    to the names in the predicates parameter.
#
# @param predicates: A dictionary of MTL.Predicate()'s.
#
# @param mode:       The specified computation mode to be used for MTL. The
#                    default mode is 'cpu_threaded'


def parse(formula: str, predicates: Predicates, mode: str = "cpu") -> Optional[StlSpecification]:
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

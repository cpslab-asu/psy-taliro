from typing import TYPE_CHECKING

from .parser import parse

if TYPE_CHECKING:
    from .parser import Predicates
    from .stlSpecification import StlSpecification

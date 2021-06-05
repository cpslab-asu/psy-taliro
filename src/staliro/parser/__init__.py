from typing import TYPE_CHECKING

from .parser import parse

if TYPE_CHECKING:
    from .parser import Predicate
    from .stlSpecification import StlSpecification

from typing import TYPE_CHECKING

from .stlSpecification import StlSpecification
from .parser import parse

if TYPE_CHECKING:
    from .parser import Predicates

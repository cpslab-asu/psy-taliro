from typing import Union

import tltk_mtl as mtl

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

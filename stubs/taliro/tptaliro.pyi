from typing import Dict, List, Optional, Sequence, Tuple, TypedDict, Union

import numpy as np
from numpy.typing import NDArray

class TaliroPredicate(TypedDict):
    name: str
    a: NDArray[np.float_]
    b: NDArray[np.float_]
    l: Optional[NDArray[np.float_]]

# The type definitions that follow should be defined in `py-taliro` package.
# However, since it is a WIP, here is sufficient. For now.
class HyDist(TypedDict):
    """Hybrid Distance Type

    Attributes:
        ds: Distance to state trajectory
        dl: Distance to location
    """

    ds: float
    dl: float

Vertex = str
AdjacencyList = Dict[Vertex, List[Vertex]]

Edge = Tuple[Vertex, Vertex]

class Guard(TypedDict):
    """The constraint of the form Ax <= b

    Attributes:
        a: A matrix
        b: b matrix
    """

    a: Union[NDArray[np.float_], float, int]
    b: Union[NDArray[np.float_], float, int]

GuardMap = Dict[Edge, Guard]

def tptaliro(
    spec: str,
    preds: Sequence[TaliroPredicate],
    st: NDArray[np.float_],
    ts: NDArray[np.float_],
    lt: Optional[NDArray[np.float_]],
    adj_list: Optional[AdjacencyList],
    guards: Optional[GuardMap],
) -> HyDist: ...

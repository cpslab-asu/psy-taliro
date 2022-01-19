from typing import Sequence, TypedDict

import numpy as np
from numpy.typing import NDArray

class TaliroPredicate(TypedDict):
    name: str
    a: NDArray[np.float_]
    b: NDArray[np.float_]

def tptaliro(
    spec: str, preds: Sequence[TaliroPredicate], st: NDArray[np.float_], ts: NDArray[np.float_]
) -> float: ...

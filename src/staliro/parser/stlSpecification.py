import sys
from typing import Dict

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

from numpy import ndarray


class StlSpecification(Protocol):
    robustness: float

    def reset(self) -> None:
        ...

    def eval_interval(self, __traces: Dict[str, ndarray], __time_stamps: ndarray) -> None:
        ...

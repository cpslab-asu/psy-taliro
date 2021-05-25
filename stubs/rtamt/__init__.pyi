from typing import List, Tuple, Dict

from numpy import ndarray

from .enumerations.options import Semantics

class _RTAMTSpecification:
    name: str
    spec: str
    semantics: Semantics
    def __init__(self, semantics: Semantics = ...): ...
    def parse(self) -> None: ...
    def pastify(self) -> None: ...
    def declare_var(self, name: str, dtype: str) -> None: ...

class STLDenseTimeSpecification(_RTAMTSpecification):
    def evaluate(
        self, *args: Tuple[str, List[Tuple[float, float]]]
    ) -> List[Tuple[float, float]]: ...

class STLDiscreteTimeSpecification(_RTAMTSpecification):
    def set_sampling_period(
        self, period: float, unit: str, tolerance: float
    ) -> None: ...
    def evaluate(self, data: Dict[str, ndarray]) -> List[Tuple[float, float]]: ...

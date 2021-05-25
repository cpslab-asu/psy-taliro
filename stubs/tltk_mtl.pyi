from typing import Dict, Optional, Any

from numpy import ndarray

_Traces = Dict[str, ndarray]

class TLTKObject:
    robustness: float
    def eval_interval(
        self, traces: _Traces, time_stamps: ndarray, param_names: Optional[Any] = ...
    ) -> None: ...
    def reset(self) -> None: ...

class Predicate(TLTKObject):
    def __init__(
        self,
        variable_name: str,
        A_Matrix: ndarray,
        bound: ndarray,
        robustness: Optional[float] = ...,
        param_name: Optional[str] = ...,
        process_type: str = ...,
        thread_pool: bool = ...,
    ) -> None: ...

class Next(TLTKObject):
    def __init__(self, subformula: TLTKObject) -> None: ...

class Global(TLTKObject):
    def __init__(
        self,
        lower_time_bound: float,
        upper_time_bound: float,
        subformula: Optional[TLTKObject] = ...,
        param_name: Optional[Any] = ...,
        process_type: str = ...,
    ) -> None: ...

class Finally(TLTKObject):
    def __init__(
        self,
        lower_time_bound: float,
        upper_time_bound: float,
        subformula: Optional[TLTKObject] = ...,
        param_name: Optional[Any] = ...,
        process_type: str = ...,
    ) -> None: ...

class Not(TLTKObject):
    def __init__(
        self, subformula: Optional[TLTKObject] = ..., process_type: str = ...
    ) -> None: ...

class And(TLTKObject):
    def __init__(
        self,
        left_subformula: Optional[TLTKObject] = ...,
        right_subformula: Optional[TLTKObject] = ...,
        process_type: str = ...,
    ) -> None: ...

class Or(TLTKObject):
    def __init__(
        self,
        left_subformula: Optional[TLTKObject] = ...,
        right_subformula: Optional[TLTKObject] = ...,
        process_type: str = ...,
    ) -> None: ...

class Implication(TLTKObject):
    def __init__(
        self,
        left_subformula: Optional[TLTKObject] = ...,
        right_subformula: Optional[TLTKObject] = ...,
        process_type: str = ...,
    ) -> None: ...

class Until(TLTKObject):
    def __init__(
        self,
        lower_time_bound: float,
        upper_time_bound: float,
        left_subformula: Optional[TLTKObject] = ...,
        right_subformula: Optional[TLTKObject] = ...,
        param_name: Optional[Any] = ...,
        process_type: str = ...,
    ) -> None: ...

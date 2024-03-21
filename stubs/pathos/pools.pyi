from pathos.abstract_launcher import AbstractWorkerPool

class ThreadPool(AbstractWorkerPool):
    def __init__(self, nodes: int = ...): ...

class ProcessPool(AbstractWorkerPool):
    def __init__(self, nodes: int = ...): ...

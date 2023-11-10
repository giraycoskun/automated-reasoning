from abc import ABC, abstractmethod

class Puzzle(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def preprocess(self):
        pass

    @abstractmethod
    def solve(self):
        pass

    @abstractmethod
    def postprocess(self):
        pass

    @abstractmethod
    def pretty_print(self):
        pass

class SearchPuzzle(Puzzle):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def preprocess(self):
        pass

    @abstractmethod
    def solve(self):
        pass
    
    @abstractmethod
    def postprocess(self):
        pass
    
    @abstractmethod
    def pretty_print(self):
        pass
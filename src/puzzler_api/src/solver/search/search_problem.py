from abc import ABC, abstractmethod


class SearchProblem(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def successor_states(self):
        pass

    @abstractmethod
    def goal_check(self):
        pass

    @abstractmethod
    def get_step_cost(self):
        pass

    @abstractmethod
    def get_heuristic_cost(self):
        pass

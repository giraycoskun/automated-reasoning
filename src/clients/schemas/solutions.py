from dataclasses import dataclass

from clients.schemas.problems import ProblemStatus

@dataclass()
class Solution:
    """Represents a solution to a problem."""

    problem_id: str
    solution_data: dict
    status: ProblemStatus
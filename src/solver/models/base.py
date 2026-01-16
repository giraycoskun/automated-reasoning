"""Problem domain models for the solver service."""

from dataclasses import dataclass, field

from clients.schemas.problems import Problem, ProblemName, ProblemType

@dataclass(kw_only=True)
class BaseProblemModel:
    """Lightweight base model shared by solver components."""

    problem_id: str = ""
    problem_name: ProblemName
    problem_type: ProblemType = ProblemType.BASE
    problem: Problem
    problem_data: dict = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        if not self.problem_id:
            raise ValueError("problem_id cannot be empty")
        if not self.problem_name:
            raise ValueError("problem_name cannot be empty")

    def write_back_solution(self, solution):
        """Write back solution to the problem model. To be overridden by subclasses."""
        return solution
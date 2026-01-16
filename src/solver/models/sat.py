from dataclasses import dataclass

from clients.schemas.problems import ProblemType
from solver.models.base import BaseProblemModel


@dataclass(kw_only=True)
class SATProblemModel(BaseProblemModel):
    """Represents a SAT problem model."""
    problem_type: ProblemType = ProblemType.SAT
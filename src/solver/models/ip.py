"""Integer Programming problem model."""

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping

from clients.schemas.problems import ProblemType
from solver.models.base import BaseProblemModel


def _validate_constraint(constraint: Mapping[str, Any]) -> bool:
    if not isinstance(constraint, Mapping):
        return False
    if (
        "coefficients" not in constraint
        or "sense" not in constraint
        or "rhs" not in constraint
    ):
        return False
    if constraint["sense"] not in {"<=", ">=", "=="}:
        return False
    if not isinstance(constraint["coefficients"], Mapping):
        return False
    return True


def _validate_objective(objective: Mapping[str, Any]) -> bool:
    if not isinstance(objective, Mapping):
        return False
    if "coefficients" not in objective or "sense" not in objective:
        return False
    if objective["sense"] not in {"minimize", "maximize"}:
        return False
    if not isinstance(objective["coefficients"], Mapping):
        return False
    return True


def _validate_variables(variables: Mapping[str, Any]) -> bool:
    if not isinstance(variables, Mapping):
        return False
    for var_info in variables.values():
        if not isinstance(var_info, Mapping):
            return False
        if var_info.get("type") not in {"Integer", "Binary", "Continuous"}:
            return False
    return True

@dataclass(kw_only=True)
class IPProblem(BaseProblemModel):
    """Represents an IP/MIP problem in the solver domain."""

    problem_type: ProblemType = ProblemType.IP
    problem_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__post_init__()
        self._validate_ip_problem_data()

    def _validate_ip_problem_data(self) -> None:
        data = self.problem_data
        if not isinstance(data, Mapping):
            raise ValueError("problem_data must be a mapping")

        objective = data.get("objective")
        constraints = data.get("constraints")
        variables = data.get("variables")

        if not _validate_objective(objective): # type: ignore
            raise ValueError("Invalid or missing objective in problem_data")
        if not isinstance(constraints, list) or not all(
            _validate_constraint(c) for c in constraints
        ):
            raise ValueError("Invalid or missing constraints in problem_data")
        if not _validate_variables(variables): # type: ignore
            raise ValueError("Invalid or missing variables in problem_data")

    def write_back_solution(self, solution):
        """Write back solution to the problem model. To be overridden by subclasses."""
        return solution
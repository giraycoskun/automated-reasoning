"""Sudoku to Integer Programming constraint mapper and models."""

from dataclasses import dataclass
import statistics
from typing import Any, Dict, List

from loguru import logger

from clients.schemas.problems import Problem, ProblemName, ProblemStatus, ProblemType
from clients.schemas.solutions import Solution
from solver.models.ip import IPProblem


@dataclass(kw_only=True)
class SudokuProblemModel(IPProblem):
    """Represents a Sudoku instance that can be converted into an IP problem."""

    problem: Problem
    problem_id: str = ""
    problem_name: ProblemName = ProblemName.SUDOKU

    def __post_init__(self) -> None:
        # Extract grid from the problem instance
        grid = getattr(self.problem, "grid", None)
        if grid is None and isinstance(
            getattr(self.problem, "problem_data", None), dict
        ):
            grid = self.problem.problem_data.get("grid")

        if grid is None:
            raise ValueError(
                "Sudoku problem must include a 'grid' to build constraints"
            )

        # Populate required parent fields from problem instance
        self.problem_id = self.problem.problem_id
        self.problem_name = ProblemName.SUDOKU
        self.problem_type = self.problem.problem_type

        # Generate IP constraints
        if self.problem.problem_type == ProblemType.IP:
            self.problem_data = sudoku_to_ip_constraints(grid)

        # Validate the complete model
        super().__post_init__()

    def write_back_solution(self, solution: Solution) -> Solution:
        """Convert IP solution back to Sudoku grid format and store in self.solution."""
        # solution.solution_data is the solver result with keys: status, solution, objective_value, statistics
        grid: List[List[int]] = ip_solution_to_sudoku_grid(
            solution.solution_data.get("variables", {})
        )
        solution_statistics = solution.solution_data.get("statistics", {})
        solution_status = solution.solution_data.get("status", "")
        solution.solution_data = {
            "grid": grid,
            "statistics": solution_statistics,
            "status": solution_status,
        }
        solution.status = ProblemStatus.SOLVED
        solution.problem_id = self.problem_id
        return solution


def sudoku_to_ip_constraints(grid: List[List[int]], size: int = 9) -> Dict[str, Any]:
    """
    Convert a Sudoku grid to an Integer Programming (IP) formulation.

    Variables:
    - Binary assignment variables x[i,j,k] where x[i,j,k]=1 means cell (i,j) contains digit k

    Constraints:
    - Each cell picks exactly one digit: sum_k x[i,j,k] == 1
    - Row uniqueness: for each row i and digit k, sum_j x[i,j,k] == 1
    - Column uniqueness: for each col j and digit k, sum_i x[i,j,k] == 1
    - Box uniqueness: for each 3x3 box and digit k, sum_{i,j in box} x[i,j,k] == 1
    - Prefilled cells: x[i,j,clue] == 1 for cells with clues

    Objective:
    - Feasibility (constant objective)
    """
    box_size = int(size**0.5)

    variables: Dict[str, Dict[str, Any]] = {}

    # Binary assignment variables x_i_j_k only
    for i in range(size):
        for j in range(size):
            for k in range(1, size + 1):
                x_name = f"x_{i}_{j}_{k}"
                variables[x_name] = {"type": "Binary", "lb": 0, "ub": 1}

    constraints: List[Dict[str, Any]] = []

    # Each cell picks exactly one digit
    for i in range(size):
        for j in range(size):
            coeffs = {f"x_{i}_{j}_{k}": 1 for k in range(1, size + 1)}
            constraints.append(
                {
                    "coefficients": coeffs,
                    "sense": "==",
                    "rhs": 1,
                    "name": f"cell_{i}_{j}_one_value",
                }
            )

    # Prefilled cells: fix the appropriate binary variable to 1
    for i in range(size):
        for j in range(size):
            clue = grid[i][j]
            if clue != 0:
                constraints.append(
                    {
                        "coefficients": {f"x_{i}_{j}_{clue}": 1},
                        "sense": "==",
                        "rhs": 1,
                        "name": f"clue_{i}_{j}",
                    }
                )

    # Row uniqueness for each digit
    for i in range(size):
        for k in range(1, size + 1):
            coeffs = {f"x_{i}_{j}_{k}": 1 for j in range(size)}
            constraints.append(
                {
                    "coefficients": coeffs,
                    "sense": "==",
                    "rhs": 1,
                    "name": f"row_{i}_digit_{k}",
                }
            )

    # Column uniqueness for each digit
    for j in range(size):
        for k in range(1, size + 1):
            coeffs = {f"x_{i}_{j}_{k}": 1 for i in range(size)}
            constraints.append(
                {
                    "coefficients": coeffs,
                    "sense": "==",
                    "rhs": 1,
                    "name": f"col_{j}_digit_{k}",
                }
            )

    # Box uniqueness for each digit
    for box_i in range(box_size):
        for box_j in range(box_size):
            for k in range(1, size + 1):
                coeffs: Dict[str, int] = {}
                for i in range(box_i * box_size, (box_i + 1) * box_size):
                    for j in range(box_j * box_size, (box_j + 1) * box_size):
                        coeffs[f"x_{i}_{j}_{k}"] = 1
                constraints.append(
                    {
                        "coefficients": coeffs,
                        "sense": "==",
                        "rhs": 1,
                        "name": f"box_{box_i}_{box_j}_digit_{k}",
                    }
                )

    # Objective: Constant (pure feasibility)
    objective = {
        "coefficients": {},
        "sense": "minimize",
    }

    logger.info(
        f"Generated IP formulation: {len(variables)} variables, {len(constraints)} constraints"
    )

    return {"objective": objective, "constraints": constraints, "variables": variables}


def ip_solution_to_sudoku_grid(
    variables: Dict[str, float], size: int = 9
) -> List[List[int]]:
    """
    Convert IP solution back to Sudoku grid format.

    Extracts values from binary assignment variables x_i_j_k.

    Args:
        variables: Dictionary mapping variable names to their values
        size: Size of the Sudoku grid (default 9)

    Returns:
        2D list representing the solved Sudoku grid
    """
    grid = [[0 for _ in range(size)] for _ in range(size)]

    for var_name, value in variables.items():
        # Parse variable name: x_i_j_k (binary assignment variables)
        parts = var_name.split("_")
        if len(parts) == 4 and parts[0] == "x":
            try:
                i = int(parts[1])
                j = int(parts[2])
                k = int(parts[3])
                # If this binary variable is set to 1, cell (i,j) contains digit k
                if round(value) == 1:
                    grid[i][j] = k
            except (ValueError, IndexError):
                continue

    return grid

    def _validate_solution():
        pass

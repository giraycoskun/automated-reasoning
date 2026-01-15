"""Puzzle data classes for the API service.

This module defines the base Puzzle class and specific puzzle implementations
like Sudoku that are used to represent puzzle instances in the system.
"""

from dataclasses import dataclass
from clients.schemas.problems import Problem, ProblemType

@dataclass(kw_only=True)
class Sudoku(Problem):
    """Sudoku puzzle representation.

    A 9x9 grid-based constraint satisfaction puzzle where each row, column,
    and 3x3 box must contain digits 1-9 exactly once.

    Attributes:
        grid: The 9x9 Sudoku grid as a string or list representation.
    """

    grid: list[str]
    problem_type: ProblemType = ProblemType.SAT
    problem_name: str = "Sudoku"
    problem_class: str = __name__

    def __post_init__(self) -> None:
        self.problem_data = {"grid": self.grid}
        super().__post_init__()

    def validate(self) -> bool:
        return super().validate()

    def preprocess(self) -> None:
        return super().preprocess()

    def postprocess(self) -> None:
        return super().postprocess()

    def stringify_problem(self) -> str:
        """Print a human-readable representation of the problem."""
        problem_str = f"Problem ID: {self.problem_id}, Type: {self.problem_type}\n"
        size = 9
        for i in range(size):
            row_idx = 0
            row = list(self.grid[i])
            for char in row:
                row_idx += 1
                if row_idx % 3 == 0 and row_idx != size:
                    problem_str += char + " | "
                else:
                    problem_str += char + " "
            if i % 3 == 2 and i != size - 1:
                problem_str += "\n------|-------|------\n"
            else:
                problem_str += "\n"
        return problem_str



if __name__ == "__main__":
    # Example Sudoku instance
    example_sudoku: Sudoku = Sudoku(
        problem_id="sudoku-001",
        grid=[
            "530070000",
            "600195000",
            "098000060",
            "800060003",
            "400803001",
            "700020006",
            "060000280",
            "000419005",
            "000080079",
        ]
    )
    example_sudoku.print_problem()

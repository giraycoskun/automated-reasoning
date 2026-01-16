"""Puzzle data classes for the API service.

This module defines the base Puzzle class and specific puzzle implementations
like Sudoku that are used to represent puzzle instances in the system.
"""

from dataclasses import dataclass
from clients.schemas.problems import Problem, ProblemType, ProblemName


@dataclass(kw_only=True)
class Sudoku(Problem):
    """Sudoku puzzle representation.

    A 9x9 grid-based constraint satisfaction puzzle where each row, column,
    and 3x3 box must contain digits 1-9 exactly once.

    Attributes:
        grid: The 9x9 Sudoku grid as a string or list representation.
    """

    grid: list[list[int]]
    problem_type: ProblemType
    problem_name: ProblemName = ProblemName.SUDOKU
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
        for i in range(len(self.grid)):
            for j in range(len(self.grid[i])):
                problem_str += str(self.grid[i][j]) + " "
                if (j + 1) % 3 == 0 and j < 8:
                    problem_str += "| "
            if (i + 1) % 3 == 0 and i < 8:
                problem_str += "\n------|-------|------\n"
            else:
                problem_str += "\n"
        problem_str = problem_str.replace(
            "0", "_"
        )  # Replace 0s with spaces for empty cells
        return problem_str


if __name__ == "__main__":
    # Example Sudoku instance
    example_sudoku: Sudoku = Sudoku(
        problem_id="sudoku-001",
        problem_type=ProblemType.IP,
        grid=[
            [5, 3, 0, 0, 7, 0, 0, 0, 0],
            [6, 0, 0, 1, 9, 5, 0, 0, 0],
            [0, 9, 8, 0, 0, 0, 0, 6, 0],
            [8, 0, 0, 0, 6, 0, 0, 0, 3],
            [4, 0, 0, 8, 0, 3, 0, 0, 1],
            [7, 0, 0, 0, 2, 0, 0, 0, 6],
            [0, 6, 0, 0, 0, 0, 2, 8, 0],
            [0, 0, 0, 4, 1, 9, 0, 0, 5],
            [0, 0, 0, 0, 8, 0, 0, 7, 9],
        ],
    )
    print(example_sudoku.stringify_problem())

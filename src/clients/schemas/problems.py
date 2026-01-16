"""Base problem classes for the API service.

This module defines the base Problem class and problem type implementations
(SAT, SearchProblem, CSPProblem, etc.) that are used to represent different
types of problems in the automated reasoning system.
"""

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from clients.config import TIMEZONE


class ProblemType(str, Enum):
    """Enumeration of supported problem types."""

    SEARCH = "search"
    CSP = "csp"
    SAT = "sat"
    IP = "ip"


class ProblemStatus(str, Enum):
    """Enumeration of problem statuses."""

    CREATED = "CREATED"
    IN_QUEUE = "IN_QUEUE"
    SOLVED = "SOLVED"
    UNSOLVABLE = "UNSOLVABLE"
    UNSUPPORTED = "UNSUPPORTED"
    FAILED = "FAILED"

class ProblemName(str, Enum):
    """Enumeration of supported problem names."""

    BASE = "base"
    SUDOKU = "sudoku"
    N_QUEENS = "n_queens"
    GRAPH_COLORING = "graph_coloring"
    KNAPSACK = "knapsack"

@dataclass(kw_only=True)
class Problem(ABC):
    """Base class for all problem types.

    This is the abstract base class for different problem types such as puzzles,
    search problems, CSP problems, and SAT problems.

    Attributes:
        problem_id: Unique identifier for the problem instance.
        problem_type: Type of problem (puzzle, search, csp, sat).
        created_at: Timestamp when the problem was created.
        status: Current status of the problem.
        input_data: Raw input data for the problem.
        solution: The solution to the problem, if solved.
        solution_time: Time taken to solve the problem in seconds.
        error_message: Error message if problem solving failed.
    """
    problem_id: str
    problem_type: ProblemType
    problem_name: ProblemName
    problem_class: str = __name__

    problem_data: dict = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=lambda: datetime.now(TIMEZONE))
    status: ProblemStatus = field(default=ProblemStatus.CREATED)

    solution: Optional[dict] = None
    solution_time: Optional[float] = None
    error_message: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate problem instance after initialization."""
        if not self.problem_id:
            raise ValueError("problem_id cannot be empty")
        if not self.problem_type:
            raise ValueError("problem_type cannot be empty")
        if not self.problem_name:
            raise ValueError("problem_name cannot be empty")

    def validate(self) -> bool:
        """Validate the problem instance.

        Returns:
            bool: True if valid, raises ValueError otherwise.
        """
        return True

    def preprocess(self) -> None:
        """Preprocess the problem data before solving."""
        pass

    def postprocess(self) -> None:
        """Postprocess the solution after solving."""
        pass

    def stringify_problem(self) -> str:
        """Convert the problem to a human-readable string."""
        return f"Problem ID: {self.problem_id}, Type: {self.problem_type}, Status: {self.status}"

    def print_problem(self) -> None:
        """Print a human-readable representation of the problem."""
        print(self.stringify_problem())
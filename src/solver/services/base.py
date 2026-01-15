# solver_service/solvers/base.py
"""Base interface for all problem solvers."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from clients.schemas.problems import Problem


class BaseSolver(ABC):
    """Abstract base class for all solvers."""
    
    @abstractmethod
    def solve(self, problem: Problem) -> Optional[Dict[str, Any]]:
        """
        Solve the given problem.
        
        Args:
            problem: The problem instance to solve
            
        Returns:
            A dictionary containing the solution, or None if unsolvable.
            The dictionary should include:
            - status: 'solved', 'unsolvable', or 'timeout'
            - solution: The actual solution data (format depends on problem type)
            - solving_time: Time taken to solve (in seconds)
            - Any other relevant metadata
        """
        pass
    
    def validate_problem(self, problem: Problem) -> bool:
        """
        Validate that the problem has all required data.
        
        Args:
            problem: The problem to validate
            
        Returns:
            True if valid, False otherwise
        """
        return problem.problem_data is not None
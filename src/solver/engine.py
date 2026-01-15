# solver_service/solver_engine.py
"""Main solver engine that dispatches problems to appropriate solvers."""

from typing import Optional, Dict, Any
from loguru import logger

from clients.schemas.problems import Problem, ProblemType
from solver_service.solvers.base import BaseSolver
from solver_service.solvers.sudoku_solver import SudokuSolver
from solver_service.solvers.sat_solver import SATSolver
from solver_service.solvers.ip_solver import IPSolver


class SolverEngine:
    """Dispatches problems to appropriate solvers based on problem type."""
    
    def __init__(self):
        # Registry of solvers by problem type
        self.solvers: Dict[ProblemType, BaseSolver] = {
            ProblemType.SAT: SATSolver(),
            ProblemType.IP: IPSolver(),
        }
        logger.info(f"Solver engine initialized with {len(self.solvers)} solvers")
        
    def solve(self, problem: Problem) -> Optional[Dict[str, Any]]:
        """
        Solve a problem using the appropriate solver.
        
        Args:
            problem: The problem to solve
            
        Returns:
            Solution dictionary or None if unsolvable
        """
        try:
            # Get the appropriate solver
            solver = self.solvers.get(problem.problem_type)
            
            if solver is None:
                logger.error(f"No solver available for problem type: {problem.problem_type}")
                return {
                    "problem_id": problem.problem_id,
                    "status": "unsupported",
                    "error": f"No solver for {problem.problem_type}"
                }
            
            # Solve the problem
            logger.debug(f"Solving {problem.problem_type} problem {problem.problem_id}")
            solution = solver.solve(problem)
            
            # Add metadata to solution
            if solution:
                solution["problem_id"] = problem.problem_id
                solution["problem_type"] = problem.problem_type.value
                
            return solution
            
        except Exception as e:
            logger.error(f"Error solving problem {problem.problem_id}: {e}")
            return {
                "problem_id": problem.problem_id,
                "status": "error",
                "error": str(e)
            }
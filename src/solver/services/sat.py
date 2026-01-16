from dataclasses import asdict
from typing import Any, Dict
from venv import logger
from pysat.formula import CNF
from pysat.solvers import Solver

from clients.schemas.problems import ProblemStatus
from clients.schemas.solutions import Solution
from solver.models.base import BaseProblemModel
from solver.models.sat import SATProblemModel


class SATSolverService:
    """Service for solving SAT problems."""

    def solve(self, problem: BaseProblemModel) -> Solution:
        """
        Solve a SAT problem.

        Args:
            problem (BaseProblemModel): The SAT problem to solve.

        Returns:
            Solution: The solution to the SAT problem.

        Example Problem Data:
        {
            "clauses": [[1, -2, 3], [-1, 2], [2, 3, -4]]
        }

        Example Solution Data:
        {
            "satisfiable": True,
            "assignment": {1: True, 2: False, 3: True, 4: False}
        }
        """

        problem = SATProblemModel(**asdict(problem))

        try:
            result = self._solve_with_pysat(problem.problem_data)
            if result.get("status") == "UNSATISFIABLE":
                return Solution(
                    problem_id=problem.problem_id,
                    solution_data=result,
                    status=ProblemStatus.FAILED,
                )
            return Solution(
                problem_id=problem.problem_id,
                solution_data=result,
                status=ProblemStatus.SOLVED,
            )
        except Exception as e:
            logger.error(f"Error solving SAT problem {problem.problem_id}: {e}")
            return Solution(
                problem_id=problem.problem_id,
                solution_data={"error": str(e)},
                status=ProblemStatus.FAILED,
            )

    def _solve_with_pysat(self, problem_data: dict) -> Dict[str, Any]:
        """
        Solve the SAT problem using PySAT.

        Args:
            problem_data (dict): The SAT problem data containing clauses.

        Returns:
            dict: The solution data with satisfiability and assignment.
        """

        clauses = problem_data.get("clauses", [])
        cnf = CNF()
        cnf.extend(clauses)
        statistics = {}
        with Solver(name="g3") as solver:
            solver.append_formula(cnf)
            satisfiable = solver.solve()
            assignment = {}
            status = "UNSATISFIABLE"
            if satisfiable:
                status = "SATISFIABLE"
                model = solver.get_model()
                for var in model:  # type: ignore
                    assignment[abs(var)] = var > 0
            statistics = solver.accum_stats()  # type: ignore
            statistics['var_count'] = len(model)  # type: ignore
        return {"status": status, "assignment": assignment, "statistics": statistics}

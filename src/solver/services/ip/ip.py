# solver_service/solvers/ip_solver.py
"""Integer Programming solver using PuLP or OR-Tools."""

from typing import Optional, Dict, Any
from loguru import logger

from clients.schemas.problems import Problem
from solver.services.base import BaseSolver

from ortools.linear_solver import pywraplp


class IPSolver(BaseSolver):
    """
    Solver for Integer Programming (IP) and Mixed Integer Programming (MIP) problems.

    Supports:
    - Linear Integer Programming
    - Mixed Integer-Linear Programming
    - Binary Integer Programming
    """

    def __init__(self, solver_backend: str = "ortools"):
        """
        Initialize IP solver.

        Args:
            solver_backend: "pulp", "ortools", or "auto"
        """
        self.backend = solver_backend
        logger.info(f"IP Solver initialized with backend: {self.backend}")

    def solve(self, problem: Problem) -> Optional[Dict[str, Any]]:
        """
        Solve an IP/MIP problem.

        Expected problem_data format:
        {
            "objective": {
                "coefficients": {var_name: coefficient},
                "sense": "minimize" or "maximize"
            },
            "constraints": [
                {
                    "coefficients": {var_name: coefficient},
                    "sense": "<=", ">=", or "==",
                    "rhs": float
                }
            ],
            "variables": {
                var_name: {
                    "type": "Integer", "Binary", or "Continuous",
                    "lb": lower_bound,
                    "ub": upper_bound
                }
            }
        }
        """
        if not self.validate_problem(problem):
            return {"status": "error", "error": "Invalid problem data"}

        try:
            result = self._solve_with_ortools(problem.problem_data)
            return result

        except Exception as e:
            logger.error(f"Error solving IP: {e}")
            return {"status": "error", "error": str(e)}

    # def _solve_with_pulp(self, problem_data: Dict[str, Any]) -> Dict[str, Any]:
    #     """Solve using PuLP."""
    #     if not PULP_AVAILABLE:
    #         return {"status": "error", "error": "PuLP not available"}

    #     try:
    #         # Create problem
    #         objective_data = problem_data["objective"]
    #         sense = (
    #             pulp.LpMinimize
    #             if objective_data["sense"] == "minimize"
    #             else pulp.LpMaximize
    #         )
    #         prob = pulp.LpProblem("IP_Problem", sense)

    #         # Create variables
    #         variables = {}
    #         for var_name, var_info in problem_data["variables"].items():
    #             var_type = var_info.get("type", "Continuous")
    #             lb = var_info.get("lb", None)
    #             ub = var_info.get("ub", None)

    #             if var_type == "Binary":
    #                 cat = pulp.LpBinary
    #             elif var_type == "Integer":
    #                 cat = pulp.LpInteger
    #             else:
    #                 cat = pulp.LpContinuous

    #             variables[var_name] = pulp.LpVariable(
    #                 var_name, lowBound=lb, upBound=ub, cat=cat
    #             )

    #         # Set objective
    #         obj_expr = pulp.lpSum(
    #             [
    #                 coef * variables[var_name]
    #                 for var_name, coef in objective_data["coefficients"].items()
    #             ]
    #         )
    #         prob += obj_expr

    #         # Add constraints
    #         for i, constraint in enumerate(problem_data["constraints"]):
    #             expr = pulp.lpSum(
    #                 [
    #                     coef * variables[var_name]
    #                     for var_name, coef in constraint["coefficients"].items()
    #                 ]
    #             )
    #             rhs = constraint["rhs"]
    #             sense = constraint["sense"]

    #             if sense == "<=":
    #                 prob += expr <= rhs, f"constraint_{i}"
    #             elif sense == ">=":
    #                 prob += expr >= rhs, f"constraint_{i}"
    #             elif sense == "==":
    #                 prob += expr == rhs, f"constraint_{i}"

    #         # Solve
    #         prob.solve(pulp.PULP_CBC_CMD(msg=0))

    #         # Extract results
    #         status = pulp.LpStatus[prob.status]

    #         if status == "Optimal":
    #             solution = {
    #                 var_name: var.varValue for var_name, var in variables.items()
    #             }
    #             return {
    #                 "status": "solved",
    #                 "objective_value": pulp.value(prob.objective),
    #                 "solution": solution,
    #             }
    #         elif status == "Infeasible":
    #             return {"status": "unsolvable", "reason": "infeasible"}
    #         elif status == "Unbounded":
    #             return {"status": "unsolvable", "reason": "unbounded"}
    #         else:
    #             return {"status": "error", "error": f"Solver status: {status}"}

    #     except Exception as e:
    #         logger.error(f"PuLP solver error: {e}")
    #         return {"status": "error", "error": str(e)}

    def _solve_with_ortools(self, problem_data: Dict[str, Any]) -> Dict[str, Any]:
        """Solve using OR-Tools."""
        try:
            # Create solver
            solver = pywraplp.Solver.CreateSolver("SCIP")
            if not solver:
                return {"status": "error", "error": "Could not create solver"}

            # Create variables
            variables = {}
            infinity = solver.infinity()

            for var_name, var_info in problem_data["variables"].items():
                var_type = var_info.get("type", "Continuous")
                lb = var_info.get("lb", -infinity)
                ub = var_info.get("ub", infinity)

                if var_type == "Binary":
                    variables[var_name] = solver.BoolVar(var_name)
                elif var_type == "Integer":
                    variables[var_name] = solver.IntVar(lb, ub, var_name)
                else:
                    variables[var_name] = solver.NumVar(lb, ub, var_name)

            # Set objective
            objective_data = problem_data["objective"]
            objective = solver.Objective()

            for var_name, coef in objective_data["coefficients"].items():
                objective.SetCoefficient(variables[var_name], coef)

            if objective_data["sense"] == "minimize":
                objective.SetMinimization()
            else:
                objective.SetMaximization()

            # Add constraints
            for i, constraint in enumerate(problem_data["constraints"]):
                ct = solver.Constraint(
                    -infinity if constraint["sense"] != ">=" else constraint["rhs"],
                    infinity if constraint["sense"] != "<=" else constraint["rhs"],
                    f"constraint_{i}",
                )

                for var_name, coef in constraint["coefficients"].items():
                    ct.SetCoefficient(variables[var_name], coef)

            # Solve
            status = solver.Solve()

            if status == pywraplp.Solver.OPTIMAL:
                solution = {
                    var_name: var.solution_value()
                    for var_name, var in variables.items()
                }
                return {
                    "status": "solved",
                    "objective_value": solver.Objective().Value(),
                    "solution": solution,
                }
            elif status == pywraplp.Solver.INFEASIBLE:
                return {"status": "unsolvable", "reason": "infeasible"}
            elif status == pywraplp.Solver.UNBOUNDED:
                return {"status": "unsolvable", "reason": "unbounded"}
            else:
                return {"status": "error", "error": "Solver failed"}

        except Exception as e:
            logger.error(f"OR-Tools solver error: {e}")
            return {"status": "error", "error": str(e)}

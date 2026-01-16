# solver_service/solvers/ip_solver.py
"""Integer Programming solver using PuLP or OR-Tools."""

from typing import Dict, Any
from loguru import logger
from ortools.linear_solver import pywraplp

from clients.schemas.problems import ProblemStatus
from solver.models.ip import IPProblem
from clients.schemas.solutions import Solution


class IPSolverService:
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

    def solve(self, problem: IPProblem) -> Solution:
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

        try:
            result = self._solve_with_ortools(problem.problem_data)
            return Solution(
                problem_id=problem.problem_id,
                solution_data=result,
                status=ProblemStatus.SOLVED if result.get("isSolved") else ProblemStatus.UNSOLVABLE,
            )

        except Exception as e:
            logger.error(f"Error solving IP: {e}")
            return Solution(
                problem_id=problem.problem_id,
                solution_data={"error": str(e)},
                status=ProblemStatus.FAILED,
            )
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

            # BUG FIX #1: Handle empty objective coefficients
            if objective_data["coefficients"]:
                for var_name, coef in objective_data["coefficients"].items():
                    if var_name in variables:  # BUG FIX #2: Check variable exists
                        objective.SetCoefficient(variables[var_name], coef)
            else:
                # For feasibility problems with no objective, set a dummy constant
                # OR-Tools requires at least something in the objective
                pass  # Empty objective is actually fine in OR-Tools

            if objective_data["sense"] == "minimize":
                objective.SetMinimization()
            else:
                objective.SetMaximization()

            # Add constraints
            for i, constraint in enumerate(problem_data["constraints"]):
                sense = constraint["sense"]
                rhs = constraint["rhs"]
                
                # BUG FIX #3: Correct constraint bounds for each sense
                if sense == "==":
                    # Equality: lb = ub = rhs
                    ct = solver.Constraint(rhs, rhs, f"constraint_{i}")
                elif sense == "<=":
                    # Less than or equal: -infinity <= expr <= rhs
                    ct = solver.Constraint(-infinity, rhs, f"constraint_{i}")
                elif sense == ">=":
                    # Greater than or equal: rhs <= expr <= infinity
                    ct = solver.Constraint(rhs, infinity, f"constraint_{i}")
                else:
                    logger.warning(f"Unknown constraint sense: {sense}")
                    continue

                for var_name, coef in constraint["coefficients"].items():
                    if var_name in variables:  # BUG FIX #4: Check variable exists
                        ct.SetCoefficient(variables[var_name], coef)
                    else:
                        logger.warning(f"Variable {var_name} not found in variables")

            # BUG FIX #5: Set time limit to prevent infinite solving
            solver.SetTimeLimit(300000)  # 5 minutes in milliseconds

            # Solve
            status = solver.Solve()

            # Collect statistics
            statistics = {
                "wall_time_ms": solver.WallTime(),
                "iterations": solver.iterations(),
                "nodes": solver.nodes(),
            }

            if status == pywraplp.Solver.OPTIMAL:
                solution = {
                    "variables": {
                        var_name: var.solution_value()
                        for var_name, var in variables.items()
                    },
                    "objective_value": solver.Objective().Value(),
                    "statistics": statistics,
                    "status": "optimal",
                    "isSolved": True,
                }
                return solution
            elif status == pywraplp.Solver.FEASIBLE:
                # BUG FIX #6: Handle FEASIBLE status (non-optimal but valid solution)
                solution = {
                    "variables": {
                        var_name: var.solution_value()
                        for var_name, var in variables.items()
                    },
                    "objective_value": solver.Objective().Value(),
                    "statistics": statistics,
                    "status": "feasible",
                    "isSolved": True,
                }
                return solution
            elif status == pywraplp.Solver.INFEASIBLE:
                return {
                    "status": "unsolvable",
                    "reason": "infeasible",
                    "statistics": statistics,
                    "isSolved": False,
                }
            elif status == pywraplp.Solver.UNBOUNDED:
                return {
                    "status": "unsolvable",
                    "reason": "unbounded",
                    "statistics": statistics,
                    "isSolved": False,
                }
            elif status == pywraplp.Solver.NOT_SOLVED:
                return {
                    "status": "error",
                    "error": "Solver did not solve (possibly timeout or other issue)",
                    "statistics": statistics,
                    "isSolved": False,
                }
            else:
                return {
                    "status": "error",
                    "error": f"Unknown solver status: {status}",
                    "statistics": statistics,
                    "isSolved": False,
                }

        except Exception as e:
            logger.error(f"OR-Tools solver error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"status": "error", "error": str(e), "isSolved": False}
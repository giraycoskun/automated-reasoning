from api.service.problems_service import save_problem
from api.util import generate_problem_id
from clients.schemas.problems import ProblemType
from clients.schemas.sudoku import Sudoku

async def create_sudoku_ip_problem(grid: list[str]) -> str:
    """
    Create a Sudoku problem instance from a 9x9 grid.
    
    Args:
        grid: A 9x9 list of lists representing the Sudoku puzzle,
              where 0 represents an empty cell.
    """
    sudoku_grid = [list(map(int, row)) for row in grid]
    sudoku: Sudoku = Sudoku(
        problem_id= await generate_problem_id(),
        grid=sudoku_grid,
        problem_type=ProblemType.IP,
    )
    await save_problem(sudoku)
    return sudoku.problem_id
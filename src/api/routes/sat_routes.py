from fastapi import APIRouter, status

from api.schemas.sudoku import SudokuCreateRequest
from api.service.problems_service import save_problem
from clients.schemas.sat.sudoku import Sudoku
from api.util import generate_problem_id

sat_router = APIRouter(prefix="/sat")


@sat_router.post(
    "/sudoku",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Sudoku puzzle created",
            "content": {
                "application/json": {
                    "example": {
                        "task_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    }
                }
            },
        }
    },
)
async def post_sudoku(sudoku_data: SudokuCreateRequest):
    """Create and submit a new Sudoku puzzle."""
    sudoku: Sudoku = Sudoku(
        problem_id=await generate_problem_id(),
        grid=sudoku_data.grid,
    )
    await save_problem(sudoku)

    return {
        "task_id": sudoku.problem_id,
    }

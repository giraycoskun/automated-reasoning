from fastapi import APIRouter, status

from api.schemas.sudoku import SudokuCreateRequest
from api.service.problems_service_sat import create_sudoku_sat_problem

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
async def post_sudoku(request: SudokuCreateRequest):
    """Create and submit a new Sudoku puzzle."""
    problem_id = await create_sudoku_sat_problem(request.grid)
    return {
        "task_id": problem_id,
    }

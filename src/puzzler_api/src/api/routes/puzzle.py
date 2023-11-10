from fastapi import APIRouter, Response, status, Depends
from typing import Annotated

from src.api.service.puzzle_service import PuzzleService
from src.api.repository.models import PuzzleIn

router = APIRouter(
    prefix="/puzzle",
    tags=["puzzle"],
    responses={status.HTTP_201_CREATED: {"description": "Puzzle created successfully."}}
)

@router.post("/")
async def create_puzzle(puzzle: PuzzleIn, puzzle_service: Annotated[PuzzleService, Depends()]) -> Response:
    await puzzle_service.create_puzzle(puzzle)
    return Response(status_code=status.HTTP_201_CREATED)

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.repository.models import Puzzle
from src.api.service.puzzle_service import PuzzleService

router = APIRouter(prefix="/status", tags=["status"])


@router.get("/{puzzle_id}", response_model=Puzzle)
async def get_status(
    puzzle_id: str, puzzle_service: Annotated[PuzzleService, Depends()]
) -> Puzzle:
    puzzle = await puzzle_service.get_puzzle(puzzle_id)
    if not puzzle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Puzzle not found")
    return puzzle

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sse_starlette.sse import EventSourceResponse

from src.api.dependencies import get_result_streamer
from src.api.events.result_stream import ResultStreamer
from src.api.repository.models import Puzzle, PuzzleIn
from src.api.service.puzzle_service import PuzzleService

router = APIRouter(
    prefix="/puzzle",
    tags=["puzzle"],
    responses={status.HTTP_201_CREATED: {"description": "Puzzle created successfully."}},
)


@router.post("/")
async def create_puzzle(
    puzzle: PuzzleIn, puzzle_service: Annotated[PuzzleService, Depends()]
) -> dict:
    puzzle_id = await puzzle_service.create_puzzle(puzzle)
    return {"id": puzzle_id}


@router.get("/{puzzle_id}", response_model=Puzzle)
async def get_puzzle(
    puzzle_id: str, puzzle_service: Annotated[PuzzleService, Depends()]
) -> Puzzle:
    puzzle = await puzzle_service.get_puzzle(puzzle_id)
    if not puzzle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Puzzle not found")
    return puzzle


@router.get("/{puzzle_id}/stream")
async def stream_puzzle(
    puzzle_id: str,
    streamer: Annotated[ResultStreamer, Depends(get_result_streamer)],
):
    async def event_generator():
        async for message in streamer.stream(puzzle_id):
            yield {"event": "update", "data": json.dumps(message)}

    return EventSourceResponse(event_generator())

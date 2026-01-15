from enum import Enum
from pydantic import BaseModel, constr


PUZZLES = ["hashi", "maze-cover"]


class PuzzleStatus(str, Enum):
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    SOLVED = "SOLVED"
    FAILED = "FAILED"


class PuzzleIn(BaseModel):
    description: str
    type: constr(regex="|".join(PUZZLES))
    input: str


class Puzzle(PuzzleIn):
    status: PuzzleStatus
    output: str | None


class PuzzleQueueMessage(BaseModel):
    puzzle_id: str


class ResultQueueMessage(BaseModel):
    puzzle_id: str
    status: PuzzleStatus
    output: str | None = None
    
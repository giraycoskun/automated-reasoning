from pydantic import BaseModel, constr


PUZZLES = [
    "hashi",
    "maze-cover"
]


class PuzzleIn(BaseModel):
    description: str
    type: constr(regex="|".join(PUZZLES))
    input: str

class Puzzle(PuzzleIn):
    status: str
    output: str
    
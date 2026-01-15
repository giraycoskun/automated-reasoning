from pydantic import BaseModel, Field, field_validator

class SudokuCreateRequest(BaseModel):
    """Request model for creating a Sudoku puzzle."""

    grid: list[str] = Field(
        ..., description="The 9x9 Sudoku grid as a string list representation."
    )

    @field_validator("grid")
    @classmethod
    def validate_grid(cls, v: list[str]) -> list[str]:
        for row in v:
            # 1️⃣ Check length
            if len(row) != 9:
                raise ValueError(
                    "Each row in the Sudoku grid must be exactly 9 characters (9x9)."
                )

            # 2️⃣ Only digits 0-9 allowed
            if not all(c.isdigit() or c == "_" for c in row):
                raise ValueError(
                    "Sudoku grid must only contain digits 0-9 or underscores for empty cells."
                )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "grid": [
                        "530070000",
                        "600195000",
                        "098000060",
                        "800060003",
                        "400803001",
                        "700020006",
                        "060000280",
                        "000419005",
                        "000080079",
                    ]
                }
            ]
        }
    }
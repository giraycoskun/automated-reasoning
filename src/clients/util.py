import msgpack
import inspect
from dataclasses import asdict
from datetime import datetime
from typing import Any

from clients.schemas.problems import Problem
from clients.schemas.sat.sudoku import Sudoku


def _msgpack_default(obj: Any) -> Any:
    """Default serializer for msgpack to handle datetime and enums."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "value"):
        return obj.value
    raise TypeError(f"Type not serializable: {type(obj)}")

def _serialize_problem(problem: Problem) -> bytes:
    """Convert a Problem instance to msgpack bytes."""
    payload = asdict(problem)
    # Extract enum values properly
    if hasattr(payload.get("problem_type"), "value"):
        payload["problem_type"] = payload["problem_type"].value
    if hasattr(payload.get("status"), "value"):
        payload["status"] = payload["status"].value
    if isinstance(payload.get("created_at"), datetime):
        payload["created_at"] = payload["created_at"].isoformat()
    return msgpack.packb(payload, use_bin_type=True, default=_msgpack_default)  # type: ignore


def _deserialize_problem(blob: bytes) -> Problem:
    """Decode msgpack bytes back to a Problem instance."""

    data = msgpack.unpackb(blob, raw=False)
    created_at = data.get("created_at")
    if isinstance(created_at, str):
        try:
            data["created_at"] = datetime.fromisoformat(created_at)
        except ValueError:
            pass

    cls_name = data.pop("problem_class", "Problem")

    # Map class name to actual class
    cls_map = {
        "Problem": Problem,
        "Sudoku": Sudoku,
        # Add other subclasses here
    }
    cls = cls_map.get(cls_name, Problem)

    # Filter data to only include valid fields for the target class
    sig = inspect.signature(cls)
    valid_fields = set(sig.parameters.keys())
    filtered_data = {k: v for k, v in data.items() if k in valid_fields}

    return cls(**filtered_data)
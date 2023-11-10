from fastapi import APIRouter, Response
from pydantic import BaseModel, constr
from uuid import UUID

router = APIRouter(
    prefix="/user",
    tags=["user"],
)

class UserIn(BaseModel):
    id: UUID
    name: constr(min_length=1, max_length=255)
    password: constr(min_length=1, max_length=255)

class UserOut(BaseModel):
    id: UUID
    name: constr(min_length=1, max_length=255)

@router.post("/")
async def create_user(user: UserIn) -> Response:
    return Response(status_code=201)

@router.put("/{user_id}")
async def update_user(user_id: UUID, user: UserIn) -> Response:
    return Response(status_code=204)

@router.get("/{user_id}")
async def get_user(user_id: UUID) -> UserOut:
    return UserOut(id=user_id, name="John Doe")

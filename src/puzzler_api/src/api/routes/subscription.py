from fastapi import APIRouter, Response
from pydantic import BaseModel

router = APIRouter(
    prefix="/subscription",
    tags=["subscription"],
)

class Subscription(BaseModel):
    id: int
    port: int
    url: str

@router.post("/")
async def create_subscription(subscription: Subscription) -> Response:
    return Response(status_code=201)

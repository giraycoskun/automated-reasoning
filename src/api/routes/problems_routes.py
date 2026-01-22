from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import PlainTextResponse, StreamingResponse

from clients.schemas.problems import Problem
from api.service.problems_service import get_problem, event_generator
from api.routes.ip_routes import ip_router
from api.routes.sat_routes import sat_router

problems_router = APIRouter(prefix="/problems", tags=["problems"])

problems_router.include_router(ip_router)
problems_router.include_router(sat_router)


@problems_router.get("/{problem_id}")
async def get_problem_route(problem_id: str) -> Problem:
    problem: Problem | None = await get_problem(problem_id)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found"
        )
    return problem


@problems_router.get("/print/{problem_id}", response_class=PlainTextResponse)
async def print_problem_route(problem_id: str) -> str:
    problem: Problem | None = await get_problem(problem_id)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found"
        )
    problem_str = problem.stringify_problem()
    return problem_str


@problems_router.get("/subscribe/{problem_id}")
async def subscribe(problem_id: str, request: Request, ttl: int = 300):
    """
    Subscribe endpoint that returns SSE stream with TTL
    Client connects with their ID and receives events

    Args:
        client_id: Unique identifier for the client
        ttl: Time to live in seconds (default: 300 = 5 minutes)
             Connection closes if no messages received within this time
    """
    return StreamingResponse(
        event_generator(problem_id, request, ttl),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        },
    )

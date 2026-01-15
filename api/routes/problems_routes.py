from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse

from clients.schemas.problems import Problem
from api.service.problems_service import get_problem
from api.routes.sat_routes import sat_router

problems_router = APIRouter(prefix="/problems", tags=["problems"])

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
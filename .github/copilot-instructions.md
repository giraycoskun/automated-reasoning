# Copilot Instructions for Automated Reasoning

## Architecture Overview

This is a **distributed puzzle solver** with two microservices:
- **API Service** ([src/api/](../src/api/)): FastAPI REST API that accepts puzzle submissions, stores them in Redis, and publishes to RabbitMQ
- **Solver Service** ([src/solver/](../src/solver/)): Multi-process consumer that pulls puzzles from RabbitMQ, solves them using CSP/search algorithms, and publishes results back

### Data Flow
1. Client POSTs puzzle → API creates record in Redis (status: CREATED) → Publishes to `puzzle-jobs` queue
2. Solver workers consume from `puzzle-jobs` → Update Redis (IN_PROGRESS) → Solve → Publish to `puzzle-results`
3. API consumes `puzzle-results` in background thread → Updates Redis → Streams results via SSE to subscribed clients

## Key Patterns

### Singleton Repositories
Repositories are **singleton instances** initialized at module level in [dependencies.py](../src/api/dependencies.py):
```python
rabbitmq_repository = RabbitMQRepository()  # Connection pool
redis_repository = RedisRepository()
```
Never instantiate these directly; use FastAPI's `Depends()` to inject them.

### RabbitMQ Connection Pooling
[RabbitMQRepository](../src/api/repository/rabbitmq_repository.py) maintains a **connection pool** (Queue of pika.BlockingConnection). Always use `_get_connection()` and `_release_connection()` to avoid leaks.

### Configuration Pattern
All config is centralized in [src/config.py](../src/config.py) using a frozen dataclass. Environment variables are loaded via `python-dotenv`. Never hardcode service endpoints or credentials.

### Puzzle Solver Pattern
All puzzle solvers in [src/solver/puzzles/](../src/solver/puzzles/) inherit from `Puzzle` abstract base class with lifecycle methods:
```python
def preprocess(self): pass  # Parse input
def solve(self): pass       # Apply CSP/search
def postprocess(self): pass # Format solution
def pretty_print(self): pass
```
Register new puzzle types in `PUZZLES` list in [models.py](../src/api/repository/models.py).

## Development Workflow

### Running Services
```bash
# API (requires Redis + RabbitMQ running)
uvicorn src.api.main:app --reload

# Solver (runs multiprocess workers)
python -m src.solver.main
```

### Dependencies
Managed via **uv** (see `pyproject.toml`). Install with:
```bash
uv sync
```

### Adding New Puzzle Type
1. Create solver in `src/solver/puzzles/<puzzle_name>.py` extending `Puzzle`
2. Add `<puzzle_name>` to `PUZZLES` in [src/api/repository/models.py](../src/api/repository/models.py)
3. Wire solving logic in `solve_puzzle()` in [solver.py](../src/solver/solver.py)

## Critical Constraints

- **Python 3.13 required** (`requires-python = ">=3.13,<3.14"`)
- **Multiprocessing in Solver**: Uses `Process` for worker pool. Avoid shared state; communicate via Redis/RabbitMQ only.
- **SSE Streaming**: [ResultStreamer](../src/api/events/result_stream.py) uses asyncio for real-time updates. Background thread bridges pika (sync) to asyncio.
- **Error Handling**: Always ACK RabbitMQ messages even on error to prevent requeue loops. Log malformed messages and continue.

## Testing & Debugging

- Logs use **loguru** with structured context (e.g., `logger.info("Puzzle {id}", id=puzzle_id)`)
- Use `/ping` endpoint to verify API health
- Check RabbitMQ queue depths and Redis keys when debugging stuck puzzles
- Set `SOLVER_WORKER_SIZE` env var to control parallelism (default: 1)

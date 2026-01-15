# Solver Service

A high-performance, multi-process, multi-threaded solver service that consumes problems from RabbitMQ and writes solutions to Redis.

## Architecture

### Multi-Process, Multi-Thread Design

```
┌─────────────────────────────────────────────────────────┐
│                    Solver Service                       │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Worker 0    │  │  Worker 1    │  │  Worker N    │ │
│  │              │  │              │  │              │ │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │ │
│  │ │ Thread 1 │ │  │ │ Thread 1 │ │  │ │ Thread 1 │ │ │
│  │ │ Thread 2 │ │  │ │ Thread 2 │ │  │ │ Thread 2 │ │ │
│  │ │ Thread 3 │ │  │ │ Thread 3 │ │  │ │ Thread 3 │ │ │
│  │ │ Thread 4 │ │  │ │ Thread 4 │ │  │ │ Thread 4 │ │ │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
         ▲                                      │
         │                                      │
    RabbitMQ Queue                         Redis Storage
    (Input Problems)                       (Solutions)
```

**Key Components:**

- **Main Process**: Orchestrates worker processes and handles graceful shutdown
- **Worker Processes**: Independent processes that consume from RabbitMQ (default: 4 workers)
- **Thread Pool per Worker**: Each worker manages multiple solver threads (default: 4 threads/worker)
- **Solver Engine**: Dispatches problems to appropriate solver implementations
- **Individual Solvers**: Specialized algorithms for different problem types

### Implemented Solvers

1. **SAT Solver** - Boolean satisfiability problems
   - Uses pycosat (fast C-based solver)
   - Fallback to DPLL algorithm if pycosat unavailable
   
2. **IP/MIP Solver** - Integer and Mixed Integer Programming
   - Supports PuLP (open source)
   - Supports OR-Tools (Google's optimization suite)
   - Handles linear, integer, and binary variables
   
3. **Sudoku Solver** - Solves Sudoku as SAT problem
   - Encodes Sudoku rules as CNF clauses
   - Uses SAT solver backend
   - Decodes solution back to 9x9 grid

### Benefits

1. **True Parallelism**: Multi-process architecture bypasses Python's GIL
2. **Scalability**: Can process 16+ problems simultaneously (4 workers × 4 threads)
3. **Fault Isolation**: Worker process crashes don't affect others
4. **Resource Control**: Per-worker prefetch limits prevent overload
5. **Graceful Shutdown**: Proper signal handling ensures no message loss

## Project Structure

```
solver_service/
├── __init__.py
├── main.py              # Service entry point
├── worker.py            # Worker process implementation
├── solver_engine.py     # Problem dispatcher
├── config.py            # Configuration
├── solvers/
│   ├── __init__.py
│   ├── base.py          # Base solver interface
│   ├── sat_solver.py    # SAT solver (pycosat/DPLL)
│   ├── ip_solver.py     # IP/MIP solver (PuLP/OR-Tools)
│   └── sudoku_solver.py # Sudoku via SAT encoding
├── Dockerfile
└── requirements.txt

clients/                  # Shared client code
├── rabbitmq_client.py
├── redis_client.py
├── util.py
├── config.py
└── schemas/
    └── problems.py
```

## Installation

### Using Docker (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Scale solver service
docker-compose up --scale solver=3
```

### Manual Installation

```bash
# Install dependencies
pip install -r solver_service/requirements.txt

# Set environment variables
export RABBITMQ_HOST=localhost
export RABBITMQ_PORT=5672
export REDIS_HOST_URL=localhost
export REDIS_PORT=6379
export NUM_WORKERS=4
export THREADS_PER_WORKER=4

# Run the service
python -m solver_service.main
```

## Configuration

Configure via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `NUM_WORKERS` | 4 | Number of worker processes |
| `THREADS_PER_WORKER` | 4 | Threads per worker |
| `RABBITMQ_HOST` | localhost | RabbitMQ hostname |
| `RABBITMQ_PORT` | 5672 | RabbitMQ port |
| `RABBITMQ_USERNAME` | guest | RabbitMQ username |
| `RABBITMQ_PASSWORD` | guest | RabbitMQ password |
| `RABBITMQ_PROBLEMS_QUEUE_NAME` | problems | Queue name |
| `REDIS_HOST_URL` | localhost | Redis hostname |
| `REDIS_PORT` | 6379 | Redis port |
| `LOG_LEVEL` | INFO | Logging level |

## Adding New Solvers

1. Create a new solver class in `solver_service/solvers/`:

```python
# solver_service/solvers/my_solver.py
from solver_service.solvers.base import BaseSolver
from clients.schemas.problems import Problem

class MySolver(BaseSolver):
    def solve(self, problem: Problem) -> dict:
        # Your solving logic here
        return {
            "status": "solved",
            "solution": {...},
            "solving_time": 1.23
        }
```

2. Register it in `solver_engine.py`:

```python
from solver_service.solvers.my_solver import MySolver

self.solvers = {
    ProblemType.MY_TYPE: MySolver(),
    # ... other solvers
}
```

## Solver Examples

### SAT Problem

```python
# Problem format
problem_data = {
    "clauses": [
        [1, 2],      # x1 OR x2
        [-1, 3],     # NOT x1 OR x3
        [-2, -3]     # NOT x2 OR NOT x3
    ],
    "num_variables": 3
}

# Solution format
{
    "status": "solved",
    "solution": [1, -2, 3],  # x1=True, x2=False, x3=True
    "solving_time": 0.002
}
```

### Sudoku Problem

```python
# Problem format (0 for empty cells)
problem_data = {
    "grid": [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        # ... 7 more rows
    ]
}

# Solution format
{
    "status": "solved",
    "solution": {
        "grid": [
            [5, 3, 4, 6, 7, 8, 9, 1, 2],
            [6, 7, 2, 1, 9, 5, 3, 4, 8],
            # ... complete solution
        ]
    },
    "solving_time": 0.123
}
```

### Integer Programming Problem

```python
# Problem format: Maximize 3x + 2y subject to constraints
problem_data = {
    "objective": {
        "coefficients": {"x": 3, "y": 2},
        "sense": "maximize"
    },
    "constraints": [
        {
            "coefficients": {"x": 1, "y": 1},
            "sense": "<=",
            "rhs": 10
        },
        {
            "coefficients": {"x": 2, "y": 1},
            "sense": "<=",
            "rhs": 15
        }
    ],
    "variables": {
        "x": {"type": "Integer", "lb": 0, "ub": None},
        "y": {"type": "Integer", "lb": 0, "ub": None}
    }
}

# Solution format
{
    "status": "solved",
    "objective_value": 28.0,
    "solution": {"x": 6.0, "y": 4.0},
    "solving_time": 0.045
}
```

1. **Enqueue**: Problems are published to RabbitMQ queue
2. **Consume**: Workers pull messages with prefetch limits
3. **Solve**: Problems dispatched to thread pool for solving
4. **Store**: Solutions written to Redis as `solution:{problem_id}`
5. **Acknowledge**: Message acknowledged or rejected with requeue

## Solution Format

Solutions are stored in Redis with msgpack encoding:

```python
{
    "problem_id": "uuid",
    "problem_type": "SUDOKU",
    "status": "solved",  # or "unsolvable", "error", "timeout"
    "solution": {
        # Problem-specific solution data
    },
    "solving_time": 1.23,
    "error": "..."  # Only if status is "error"
}
```

## Monitoring

### Logs

Each worker logs with its ID for easy tracking:

```
Worker 0 processing problem abc123 (type: SUDOKU)
Worker 1 solved problem def456 in 2.34s
Worker 2 error: timeout on problem ghi789
```

### RabbitMQ Management UI

Access at `http://localhost:15672` (guest/guest) to monitor:
- Queue depth
- Message rates
- Consumer connections

### Redis

Check stored solutions:

```bash
# List all solutions
redis-cli KEYS "solution:*"

# Get specific solution
redis-cli GET "solution:{problem_id}"
```

## Performance Tuning

### For CPU-bound problems (e.g., Sudoku, SAT)
- Increase `NUM_WORKERS` (match CPU cores)
- Keep `THREADS_PER_WORKER` moderate (2-4)

### For I/O-bound problems
- Keep `NUM_WORKERS` lower
- Increase `THREADS_PER_WORKER` (8-16)

### For mixed workloads
- Balance both: `NUM_WORKERS=4`, `THREADS_PER_WORKER=4`
- Total concurrent jobs: 16

## Graceful Shutdown

The service handles `SIGINT` and `SIGTERM` gracefully:

1. Signals all workers to stop consuming
2. Workers finish current tasks
3. Incomplete messages are requeued
4. Connections closed cleanly

```bash
# Stop gracefully
docker-compose down

# Or with manual run
kill -SIGTERM <pid>
```

## Troubleshooting

### Worker not processing messages
- Check RabbitMQ connection
- Verify queue name matches
- Check worker logs for errors

### Solutions not appearing in Redis
- Verify Redis connection
- Check for serialization errors
- Ensure problem_id is correct

### High memory usage
- Reduce `NUM_WORKERS` or `THREADS_PER_WORKER`
- Add memory limits in docker-compose
- Check for memory leaks in solvers

## License

MIT
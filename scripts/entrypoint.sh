#!/bin/bash
set -e

# Configuration from environment
API_PORT=${API_PORT:-8000}
SOLVER_WORKER_SIZE=${SOLVER_WORKER_SIZE:-1}
LOG_LEVEL=${LOG_LEVEL:-INFO}

echo "=== Automated Reasoning Services ==="
echo "API_PORT: $API_PORT"
echo "SOLVER_WORKER_SIZE: $SOLVER_WORKER_SIZE"
echo "LOG_LEVEL: $LOG_LEVEL"
echo "PYTHONPATH: $PYTHONPATH"
echo "======================================"

# Trap signals for graceful shutdown
trap 'echo "Shutting down services..."; kill $API_PID $SOLVER_PID 2>/dev/null; exit 0' SIGTERM SIGINT

# Start FastAPI API service
echo "Starting FastAPI API service on port $API_PORT..."
/root/.local/bin/uv run uvicorn src.api.main:app \
    --host 0.0.0.0 \
    --port "$API_PORT" \
    --log-level "$(echo $LOG_LEVEL | tr '[:upper:]' '[:lower:]')" &
API_PID=$!
echo "API service started with PID $API_PID"

# Wait a moment for API to start before solver
sleep 2

# Start Solver service with configurable worker pool
echo "Starting Solver service with $SOLVER_WORKER_SIZE worker(s)..."
SOLVER_WORKER_SIZE="$SOLVER_WORKER_SIZE" \
/root/.local/bin/uv run python -m src.solver.main &
SOLVER_PID=$!
echo "Solver service started with PID $SOLVER_PID"

echo "All services running. Press Ctrl+C to stop."
echo ""

# Wait for both processes and monitor for crashes
while true; do
    if ! kill -0 $API_PID 2>/dev/null; then
        echo "ERROR: API service crashed!"
        kill $SOLVER_PID 2>/dev/null || true
        exit 1
    fi
    if ! kill -0 $SOLVER_PID 2>/dev/null; then
        echo "ERROR: Solver service crashed!"
        kill $API_PID 2>/dev/null || true
        exit 1
    fi
    sleep 5
done
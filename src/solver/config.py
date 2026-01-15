import os
from dotenv import load_dotenv

load_dotenv()


SOLVER_NUM_WORKERS: int = int(os.getenv("SOLVER_NUM_WORKERS", "4"))
SOLVER_THREADS_PER_WORKER: int = int(os.getenv("SOLVER_THREADS_PER_WORKER", "2"))
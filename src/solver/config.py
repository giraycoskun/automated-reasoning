import os
from dotenv import load_dotenv

load_dotenv()


SOLVER_NUM_WORKERS: int = int(os.getenv("SOLVER_NUM_WORKERS", "2"))

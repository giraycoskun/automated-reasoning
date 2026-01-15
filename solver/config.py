import os
from dotenv import load_dotenv

load_dotenv()


SOLVER_WORKER_COUNT: int = int(os.getenv("SOLVER_WORKER_COUNT", "4"))

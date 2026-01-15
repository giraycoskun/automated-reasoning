# api/config.py
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import os
load_dotenv()

ENVIRONMENT = "dev"

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
LOG_RETENTION = os.getenv("LOG_RETENTION", "7 days")
LOG_ROTATION = os.getenv("LOG_ROTATION", "10 MB")

TIMEZONE= ZoneInfo(os.getenv("TIMEZONE", "Europe/Berlin"))

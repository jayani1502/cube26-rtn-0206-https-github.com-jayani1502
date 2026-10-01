import os
import logging

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ReturnsManager")

DB_PATH = "submissions/jayani1502/returns_audit.db"
CSV_PATH = "data/returns_sample.csv"
MODEL_NAME = "gemini-2.5-flash"
TEMPERATURE = 0.1

import logging
import os
import sys
from datetime import datetime

LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"

log_dir = 'logs'

try:
    from from_root import from_root
    logs_path = os.path.join(from_root(), log_dir)
except Exception:
    # Fallback when running inside Docker container or environments without .git anchor
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    logs_path = os.path.join(base_dir, log_dir)

os.makedirs(logs_path, exist_ok=True)

log_file_path = os.path.join(logs_path, LOG_FILE)

logging.basicConfig(
    format="[ %(asctime)s ] %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler(sys.stdout)
    ]
)
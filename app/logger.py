import logging
from logging.handlers import RotatingFileHandler
import os

# Folder to store logs
LOG_FOLDER = "logs"
os.makedirs(LOG_FOLDER, exist_ok=True)

# Create logger
logger = logging.getLogger("focus_game")
logger.setLevel(logging.DEBUG)

# Format for logs
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# File handler with rotation
file_handler = RotatingFileHandler(
    f"{LOG_FOLDER}/app.log", maxBytes=1000000, backupCount=5
)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

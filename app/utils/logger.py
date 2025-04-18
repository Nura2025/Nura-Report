import logging

# Setting up a basic configuration for logging
logging.basicConfig(
    level=logging.INFO,  # Default logging level (can be set to DEBUG, ERROR, etc.)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Format for logs
    handlers=[
        logging.StreamHandler(),  # Log to the console
        logging.FileHandler("app.log")  # Optionally, log to a file
    ]
)

# Create logger instance
logger = logging.getLogger(__name__)

# Example usage:
# logger.info("This is an info message")
# logger.error("This is an error message")

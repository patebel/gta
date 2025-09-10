import logging
import os


def log_metrics(title, metric, logger):
    """
    Logs the metrics including the title, metric value, and a separator line.
    """
    logger.info("----- %s -----", title)
    logger.info("metric: %s", metric)
    logger.info("------------------------")


def setup_logger(log_file: str) -> logging.Logger:
    """
    Creates and returns a logger that writes to the specified log file.
    """
    logger = logging.getLogger(os.path.basename(log_file))
    logger.setLevel(logging.INFO)
    # Remove any existing handlers for this logger.
    if logger.hasHandlers():
        logger.handlers.clear()
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

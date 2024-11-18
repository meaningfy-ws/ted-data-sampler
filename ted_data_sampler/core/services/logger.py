import logging
import time
from logging import Logger
from typing import List, TextIO


def setup_logger(output_file_paths: List[TextIO], log_level: int = logging.INFO) -> Logger:
    logger: Logger = logging.getLogger()
    logger.setLevel(log_level)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - [%(filename)s:%(lineno)d] - %(message)s")
    for output_file_path in output_file_paths:
        stream_handler = logging.StreamHandler(output_file_path)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger

def execute_function_with_logging_execution_time(logger: Logger, func, *args, **kwargs):
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    execution_time = end_time - start_time
    message = f"Function '{func.__name__}' executed in {execution_time:.4f} seconds"
    logger.info(message)
    return result
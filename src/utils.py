import logging
import sys
import pathlib
from src.schemas import settings


def get_logger(logger_name: None) -> logging.Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(settings().LOG_LEVEL)

    stream_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    stream_handler.setFormatter(fmt=formatter)

    log_file: pathlib.Path = pathlib.Path(settings().LOG_FILE_PATH)

    if not log_file.exists():
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.touch()

    file_handler = logging.FileHandler(settings().LOG_FILE_PATH, "a", "utf-8")
    file_handler.setFormatter(fmt=formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    return logger

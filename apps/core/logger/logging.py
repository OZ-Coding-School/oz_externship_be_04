import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

try:
    from django.conf import settings

    ENV = getattr(settings, "ENV", "development")
    BASE_DIR = Path(settings, "BASE_DIR", Path(__file__).resolve().parent.parent.parent)
except Exception:
    ENV = "development"
    BASE_DIR = Path(__file__).resolve().parent.parent.parent


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    log_level = logging.DEBUG if ENV == "development" else logging.INFO
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(exist_ok=True)

    safe_name = name.replace(".", "_")
    file_path = log_dir / f"{safe_name}.log"

    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=3 * 1024 * 1024,
        backupCount=2,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)

    if ENV == "development":
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)

    return logger

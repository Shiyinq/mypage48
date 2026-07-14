import logging
import os
import sys
from logging import Logger

from .config import RecorderConfig


def setup_logging(config: RecorderConfig) -> tuple[Logger, Logger, Logger]:
    os.makedirs(config.logs_dir, exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(name)s] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    rec = logging.getLogger("recorder")
    upl = logging.getLogger("uploader")
    notif = logging.getLogger("notify")
    theater = logging.getLogger("theater")
    heartbeat = logging.getLogger("heartbeat")

    rec.setLevel(config.log_level.upper())
    upl.setLevel(config.log_level.upper())
    notif.setLevel(config.log_level.upper())
    theater.setLevel(config.log_level.upper())
    heartbeat.setLevel(config.log_level.upper())

    _add_handler(
        rec, formatter, config.log_mode, os.path.join(config.logs_dir, "recorder.log")
    )
    _add_handler(
        upl, formatter, config.log_mode, os.path.join(config.logs_dir, "uploader.log")
    )
    _add_handler(
        notif, formatter, config.log_mode, os.path.join(config.logs_dir, "notify.log")
    )
    _add_handler(
        theater,
        formatter,
        config.log_mode,
        os.path.join(config.logs_dir, "theater.log"),
    )
    _add_handler(
        heartbeat,
        formatter,
        config.log_mode,
        os.path.join(config.logs_dir, "heartbeat.log"),
    )

    return rec, upl, theater


def _add_handler(
    logger: Logger, formatter: logging.Formatter, mode: str, file_path: str
):
    if mode == "file":
        handler = logging.FileHandler(file_path)
    else:
        handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

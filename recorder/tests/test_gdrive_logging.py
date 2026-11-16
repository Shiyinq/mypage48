import logging
from types import SimpleNamespace

import pytest

from recorder.src.logging_config import setup_logging


@pytest.mark.parametrize("mode", ["stdout", "file"])
def test_gdrive_respects_log_mode(tmp_path, mode, capsys):
    names = ("recorder", "uploader", "notify", "theater", "heartbeat", "gdrive")
    previous = {
        name: (list(logging.getLogger(name).handlers), logging.getLogger(name).level)
        for name in names
    }
    try:
        setup_logging(
            SimpleNamespace(logs_dir=str(tmp_path), log_level="INFO", log_mode=mode)
        )
        logger = logging.getLogger("gdrive")
        added = [h for h in logger.handlers if h not in previous["gdrive"][0]]
        assert len(added) == 1
        logger.info("Drive cooldown reminder")
        added[0].flush()
        if mode == "file":
            assert isinstance(added[0], logging.FileHandler)
            assert "Drive cooldown reminder" in (tmp_path / "gdrive.log").read_text()
            assert "Drive cooldown reminder" not in capsys.readouterr().out
        else:
            assert isinstance(added[0], logging.StreamHandler)
            assert not isinstance(added[0], logging.FileHandler)
            assert "Drive cooldown reminder" in capsys.readouterr().out
            assert not (tmp_path / "gdrive.log").exists()
        for path in tmp_path.glob("*.log"):
            if path.name != "gdrive.log":
                assert "Drive cooldown reminder" not in path.read_text()
    finally:
        for name, (handlers, level) in previous.items():
            logger = logging.getLogger(name)
            for handler in list(logger.handlers):
                if handler not in handlers:
                    logger.removeHandler(handler)
                    handler.close()
            logger.setLevel(level)

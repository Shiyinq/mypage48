import asyncio
import logging
import os
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic import ValidationError

from recorder import main
from recorder.src.config import RecorderConfig
from recorder.src.heartbeat import run_heartbeat
from recorder.src.logging_config import setup_logging

DEFAULTS = {
    "ytpublic_enabled": False,
    "ytpublic_dry_run": True,
    "ytpublic_poll_interval": 900,
    "ytpublic_base_delay_hours": 72,
    "ytpublic_buffer_hours": 8,
    "ytpublic_exclude_video_ids": "",
    "ytpublic_max_updates_per_day": 80,
    "ytpublic_max_updates_per_scan": 5,
    "ytpublic_update_interval_seconds": 30,
    "ytpublic_daily_quota_budget": 5000,
}


@pytest.fixture(autouse=True)
def isolate_config(monkeypatch):
    monkeypatch.setitem(RecorderConfig.model_config, "env_file", None)
    for name in os.environ:
        if name.startswith("REC_"):
            monkeypatch.delenv(name)


def test_defaults():
    config = RecorderConfig()
    for name, value in DEFAULTS.items():
        assert getattr(config, name) == value
    assert config.ytpublic_excluded_video_ids == set()


def test_environment(monkeypatch):
    values = {
        "ytpublic_enabled": True,
        "ytpublic_dry_run": False,
        "ytpublic_poll_interval": 1200,
        "ytpublic_base_delay_hours": 96,
        "ytpublic_buffer_hours": 12,
        "ytpublic_exclude_video_ids": " abcDEF_-123, ,abcDEF_-123,zyxWV_987-6 ",
        "ytpublic_max_updates_per_day": 20,
        "ytpublic_max_updates_per_scan": 2,
        "ytpublic_update_interval_seconds": 60,
        "ytpublic_daily_quota_budget": 2000,
    }
    for name, value in values.items():
        monkeypatch.setenv(f"REC_{name.upper()}", str(value))
    config = RecorderConfig()
    for name, value in values.items():
        assert getattr(config, name) == value
    assert config.ytpublic_excluded_video_ids == {"abcDEF_-123", "zyxWV_987-6"}


@pytest.mark.parametrize(
    "name,minimum",
    [
        ("ytpublic_poll_interval", 60),
        ("ytpublic_base_delay_hours", 72),
        ("ytpublic_buffer_hours", 0),
        ("ytpublic_max_updates_per_day", 1),
        ("ytpublic_max_updates_per_scan", 1),
        ("ytpublic_update_interval_seconds", 0),
        ("ytpublic_daily_quota_budget", 51),
    ],
)
def test_numeric_boundaries(name, minimum, monkeypatch):
    assert getattr(RecorderConfig(**{name: minimum}), name) == minimum
    with pytest.raises(ValidationError):
        RecorderConfig(**{name: minimum - 1})
    monkeypatch.setenv(f"REC_{name.upper()}", str(minimum - 1))
    with pytest.raises(ValidationError):
        RecorderConfig()


@pytest.mark.parametrize(
    "value",
    [
        "short",
        "abcdefghijkl",
        "../abcdefgh",
        "abcdefghij!",
        "abcdefghijé",
        "abc defghij",
    ],
)
def test_invalid_exclusions_rejected(value):
    config = RecorderConfig(ytpublic_exclude_video_ids=f"abcDEF_-123,{value}")
    with pytest.raises(ValueError, match="11-character YouTube IDs"):
        _ = config.ytpublic_excluded_video_ids


def test_legacy_fields_remain_unconstrained():
    config = RecorderConfig(poll_interval=0, max_concurrent_uploads=0)
    assert config.poll_interval == 0
    assert config.max_concurrent_uploads == 0


@pytest.mark.parametrize("mode", ["stdout", "file"])
def test_logging(mode, tmp_path, capsys):
    names = (
        "recorder",
        "uploader",
        "notify",
        "theater",
        "heartbeat",
        "gdrive",
        "ytpublic",
    )
    previous = {
        name: (list(logging.getLogger(name).handlers), logging.getLogger(name).level)
        for name in names
    }
    try:
        for name in names:
            logging.getLogger(name).handlers = []
        result = setup_logging(
            RecorderConfig(log_mode=mode, logs_dir=str(tmp_path), log_level="DEBUG")
        )
        assert tuple(logger.name for logger in result) == (
            "recorder",
            "uploader",
            "theater",
        )
        logger = logging.getLogger("ytpublic")
        assert logger.level == logging.DEBUG
        logger.info("publication test")
        if mode == "file":
            assert "publication test" in (tmp_path / "ytpublic.log").read_text()
            assert "publication test" not in capsys.readouterr().out
        else:
            assert "publication test" in capsys.readouterr().out
            assert not (tmp_path / "ytpublic.log").exists()
    finally:
        for name, (handlers, level) in previous.items():
            logger = logging.getLogger(name)
            for handler in logger.handlers:
                handler.close()
            logger.handlers = handlers
            logger.setLevel(level)


@pytest.mark.parametrize("mode", ["gdrive", "ytpublic"])
def test_standalone_heartbeat_skips_backend(mode):
    with patch("recorder.src.heartbeat.httpx.AsyncClient") as client:
        asyncio.run(run_heartbeat(RecorderConfig(), mode, asyncio.Event()))
    client.assert_not_called()


@pytest.mark.parametrize(
    "mode", ["record", "upload", "theater", "gdrive", "ytpublic", "all"]
)
def test_cli_mode(mode, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["recorder", "--mode", mode])
    assert main.parse_args().mode == mode


def test_cli_default_remains_all(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["recorder"])
    assert main.parse_args().mode == "all"


@pytest.mark.parametrize(
    "mode", ["record", "upload", "theater", "gdrive", "ytpublic", "all"]
)
def test_mode_dispatch(mode, monkeypatch):
    config = RecorderConfig()
    monkeypatch.setattr(main, "RecorderConfig", lambda: config)
    monkeypatch.setattr(main, "setup_logging", lambda config: (Mock(), Mock(), Mock()))
    heartbeat = AsyncMock()
    monkeypatch.setattr(main, "run_heartbeat", heartbeat)
    workers = {}
    for name in (
        "RecordingManager",
        "Watcher",
        "NewsChecker",
        "ScheduleChecker",
        "BirthdayChecker",
        "IdnLivePlusChecker",
        "TheaterWatcher",
    ):
        workers[name] = Mock(return_value=SimpleNamespace(run=AsyncMock()))
        monkeypatch.setattr(main, name, workers[name])

    # Stub the pending service implementation without importing or calling APIs.
    services = {}
    for package, class_name in (
        ("ytpublic", "YTPublicService"),
        ("gdrive", "GDriveService"),
    ):
        module = ModuleType(f"recorder.src.{package}.service")
        service = Mock(return_value=SimpleNamespace(run=AsyncMock()))
        setattr(module, class_name, service)
        monkeypatch.setitem(sys.modules, module.__name__, module)
        services[package] = service

    async def run():
        loop = asyncio.get_running_loop()
        with patch.object(loop, "add_signal_handler"):
            await main.main(SimpleNamespace(mode=mode))

    asyncio.run(run())
    expected = {
        "RecordingManager": mode in ("all", "record"),
        "Watcher": mode in ("all", "upload"),
        **{
            name: mode in ("all", "theater")
            for name in (
                "NewsChecker",
                "ScheduleChecker",
                "BirthdayChecker",
                "IdnLivePlusChecker",
                "TheaterWatcher",
            )
        },
    }
    for name, worker in workers.items():
        assert worker.call_count == int(expected[name])
    assert services["ytpublic"].call_count == int(mode == "ytpublic")
    assert services["gdrive"].call_count == int(mode in ("all", "gdrive"))
    assert heartbeat.await_count == int(mode not in ("gdrive", "ytpublic"))
    if mode == "ytpublic":
        services["ytpublic"].assert_called_once_with(config)
        stop_event = services["ytpublic"].return_value.run.call_args.args[0]
        assert isinstance(stop_event, asyncio.Event)
        services["ytpublic"].return_value.run.assert_awaited_once_with(stop_event)

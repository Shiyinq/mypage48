"""Cooldown reminders must not follow the frequent queue scan interval."""

import asyncio
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from recorder.src.gdrive import youtube_worker
from recorder.src.gdrive.youtube_worker import COOLDOWN_LOG_INTERVAL, YouTubeWorker
from recorder.src.upload.youtube_uploader import QuotaExceededError


@pytest.fixture
def worker(tmp_path):
    config = SimpleNamespace(
        logs_dir=str(tmp_path / "logs"),
        recordings_dir=str(tmp_path / "recordings"),
        google_client_id="client",
        google_client_secret="secret",
        youtube_refresh_token="token",
    )
    return YouTubeWorker(config, None)


def test_restored_cooldown_logs_at_most_every_six_hours(worker, monkeypatch, caplog):
    clock = {"wall": 1000, "monotonic": 0}
    monkeypatch.setattr(youtube_worker.time, "time", lambda: clock["wall"])
    monkeypatch.setattr(youtube_worker.time, "monotonic", lambda: clock["monotonic"])
    worker.cooldown_path.parent.mkdir(parents=True)
    worker.cooldown_path.write_text(str(1000 + 86400))
    caplog.set_level(logging.INFO, logger="gdrive")

    assert worker._blocked()
    assert "24h 0m remaining" in caplog.text
    assert len(caplog.records) == 1
    for elapsed in (15, 60, 3600, COOLDOWN_LOG_INTERVAL - 1):
        clock.update(wall=1000 + elapsed, monotonic=elapsed)
        assert worker._blocked()
    assert len(caplog.records) == 1

    clock.update(wall=1000 + COOLDOWN_LOG_INTERVAL, monotonic=COOLDOWN_LOG_INTERVAL)
    assert worker._blocked()
    assert len(caplog.records) == 2
    assert "18h 0m remaining" in caplog.records[-1].message
    assert worker._blocked()
    assert len(caplog.records) == 2


def test_cooldown_end_logs_once_without_claiming_upload_started(worker, caplog):
    caplog.set_level(logging.INFO, logger="gdrive")
    worker._report_cooldown(0, 100)
    assert not caplog.records
    worker._report_cooldown(200, 100)
    worker._report_cooldown(200, 200)
    worker._report_cooldown(200, 201)
    assert len(caplog.records) == 2
    assert (
        "cooldown ended; checking Drive-to-YouTube queue" in caplog.records[-1].message
    )


def test_quota_warning_starts_reminder_interval(worker, monkeypatch, caplog):
    clock = {"monotonic": 0}
    monkeypatch.setattr(youtube_worker.time, "monotonic", lambda: clock["monotonic"])
    monkeypatch.setattr(
        worker, "_process_inner", AsyncMock(side_effect=QuotaExceededError)
    )
    caplog.set_level(logging.INFO, logger="gdrive")
    asyncio.run(worker._process({}, {"archive_key": "a" * 64}, 0))
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.WARNING
    assert worker._blocked()
    assert len(caplog.records) == 1

    clock["monotonic"] = COOLDOWN_LOG_INTERVAL
    assert worker._blocked()
    assert len(caplog.records) == 2
    assert "quota cooldown active" in caplog.records[-1].message

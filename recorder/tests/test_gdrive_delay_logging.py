import logging
from types import SimpleNamespace

import pytest

from recorder.src.gdrive import youtube_worker

from recorder.src.gdrive.youtube_worker import YouTubeWorker


@pytest.fixture
def worker(tmp_path):
    return YouTubeWorker(
        SimpleNamespace(
            logs_dir=tmp_path / "logs",
            recordings_dir=tmp_path / "recordings",
            google_client_id="client",
            google_client_secret="secret",
            youtube_refresh_token="token",
        ),
        None,
    )


def test_delay_announced_once_not_each_scan_or_every_six_hours(worker, caplog):
    caplog.set_level(logging.INFO, logger="gdrive")
    deadline = 1000 + 12 * 3600
    worker._report_upload_delay(deadline, 1000)
    for elapsed in (15, 60, 3600, 6 * 3600, 11 * 3600):
        worker._report_upload_delay(deadline, 1000 + elapsed)
    assert len(caplog.records) == 1
    assert "12h 0m remaining" in caplog.text

    worker._report_upload_delay(deadline, deadline)
    worker._report_upload_delay(deadline, deadline + 1)
    assert len(caplog.records) == 2
    assert "upload delay ended" in caplog.records[-1].message

    worker._report_upload_delay(deadline + 3600, deadline + 1)
    assert len(caplog.records) == 3
    assert "1h 0m remaining" in caplog.records[-1].message


def test_disabled_or_expired_delay_has_no_wait_message(worker, caplog):
    caplog.set_level(logging.INFO, logger="gdrive")
    worker._report_upload_delay(0, 1000)
    worker._report_upload_delay(900, 1000)
    assert not caplog.records


def test_restored_delay_logs_once_and_blocks_admission(worker, monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger="gdrive")
    clock = {"now": 1000}
    monkeypatch.setattr(youtube_worker.time, "time", lambda: clock["now"])
    worker.timing_path.parent.mkdir(parents=True)
    worker.timing_path.write_text("4600.0")
    assert worker._blocked()
    assert worker._blocked()
    assert len(caplog.records) == 1
    assert "1h 0m remaining" in caplog.text
    clock["now"] = 4600
    assert not worker._blocked()
    assert not worker._blocked()
    assert len(caplog.records) == 2


def test_plain_timestamp_format_and_no_legacy_json_migration(worker, monkeypatch):
    monkeypatch.setattr(youtube_worker.time, "time", lambda: 1000)
    worker.timing_path.parent.mkdir(parents=True)
    legacy = worker.timing_path.parent / ".gdrive-youtube-timing.json"
    legacy.write_text('{"next_upload_time": 9999999999}')
    assert worker.timing_path.name == ".gdrive_youtube_delay"
    assert worker._read_upload_deadline() == 0
    assert not worker._blocked()
    assert not worker.timing_path.exists()
    assert legacy.exists()

    worker.timing_path.write_text("4600.0")
    assert worker._read_upload_deadline() == 4600
    assert worker._blocked()


def test_quota_takes_precedence_without_false_delay_end(worker, caplog):
    caplog.set_level(logging.INFO, logger="gdrive")
    worker._report_upload_delay(4600, 1000, cooldown=90000)
    worker._report_upload_delay(4600, 4600, cooldown=90000)
    assert not caplog.records

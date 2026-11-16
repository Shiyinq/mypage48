import asyncio
from unittest.mock import patch

import pytest

from recorder.src.config import RecorderConfig
from recorder.src.upload.watcher import Watcher


@pytest.fixture(autouse=True)
def disable_env_file(monkeypatch):
    monkeypatch.setitem(RecorderConfig.model_config, "env_file", None)


def test_priority_config(monkeypatch):
    monkeypatch.setenv("REC_YOUTUBE_UPLOAD_PRIORITY", " Erine,OLINE,,fritzy,erine, ")
    config = RecorderConfig()
    assert config.youtube_upload_priority_ranks == {
        "erine": 0,
        "oline": 1,
        "fritzy": 2,
    }


@pytest.mark.parametrize(
    "priority,nicknames,expected",
    [
        (
            "erine,oline,fritzy,",
            ["Oline", " Erine ", "erine", "Fritzy", None],
            ["2", "1", "0", "3", "4"],
        ),
        ("", ["Oline", "Erine", "Erine", "Fritzy", None], ["4", "2", "0", "3", "1"]),
        (
            "erine,oline,fritzy",
            ["Fritzy", "other", "other", "Fritzy", None],
            ["0", "3", "4", "2", "1"],
        ),
    ],
)
def test_youtube_queue_order(tmp_path, priority, nicknames, expected):
    config = RecorderConfig(
        youtube_upload_priority=priority,
        logs_dir=str(tmp_path),
    )
    watcher = Watcher(config)
    candidates = []
    for index, (nickname, size) in enumerate(zip(nicknames, [30, 10, 50, 20, 100])):
        live_id = str(index)
        folder = tmp_path / live_id
        folder.mkdir()
        (folder / ".r2_done").touch()
        (folder / f"{live_id}.mp4").write_bytes(b"x" * size)
        candidates.append(({"member_nickname": nickname}, live_id, str(folder)))

    queued = []

    def capture_task(coroutine):
        queued.append(coroutine.cr_frame.f_locals["live_id"])
        coroutine.close()

    with patch.object(watcher, "_iter_pending", return_value=iter(candidates)):
        with patch("recorder.src.upload.watcher.asyncio.create_task", capture_task):
            asyncio.run(watcher._scan_queue(str(tmp_path)))

    assert queued == expected

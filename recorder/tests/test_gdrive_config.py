import asyncio
from unittest.mock import patch

import pytest

from recorder.src.config import RecorderConfig
from recorder.src.heartbeat import run_heartbeat


@pytest.fixture(autouse=True)
def isolate_config(monkeypatch):
    monkeypatch.setitem(RecorderConfig.model_config, "env_file", None)
    for name in (
        "BACKUP_TO_GDRIVE",
        "GDRIVE_TO_YOUTUBE",
        "GDRIVE_REFRESH_TOKEN",
        "GDRIVE_DELETE_AFTER_YOUTUBE_UPLOAD",
        "GDRIVE_KEEP_MEMBERS",
    ):
        monkeypatch.delenv(f"REC_{name}", raising=False)


def test_gdrive_defaults():
    config = RecorderConfig()
    assert config.backup_to_gdrive is False
    assert config.gdrive_to_youtube is False
    assert config.gdrive_refresh_token == ""
    assert config.gdrive_delete_after_youtube_upload is False
    assert config.gdrive_keep_members == ""
    assert config.gdrive_keep_members_normalized == set()


def test_gdrive_environment(monkeypatch):
    monkeypatch.setenv("REC_BACKUP_TO_GDRIVE", "true")
    monkeypatch.setenv("REC_GDRIVE_TO_YOUTUBE", "true")
    monkeypatch.setenv("REC_GDRIVE_REFRESH_TOKEN", "test-token")
    monkeypatch.setenv("REC_GDRIVE_DELETE_AFTER_YOUTUBE_UPLOAD", "true")
    monkeypatch.setenv("REC_GDRIVE_KEEP_MEMBERS", " Erine,OLINE,,erine, Straße, ")
    config = RecorderConfig()
    assert config.backup_to_gdrive is True
    assert config.gdrive_to_youtube is True
    assert config.gdrive_refresh_token == "test-token"
    assert config.gdrive_delete_after_youtube_upload is True
    assert config.gdrive_keep_members_normalized == {"erine", "oline", "strasse"}


def test_gdrive_heartbeat_does_not_contact_backend():
    with patch("recorder.src.heartbeat.httpx.AsyncClient") as client:
        asyncio.run(run_heartbeat(RecorderConfig(), "gdrive", asyncio.Event()))
    client.assert_not_called()

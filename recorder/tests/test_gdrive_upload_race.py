"""Stale upload admission and shared ownership regressions (no network)."""

import asyncio
import json
import shutil
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from recorder.src.process_lock import async_recording_lock, recording_lock
from recorder.src.upload import watcher as module
from recorder.src.upload.watcher import Watcher


@pytest.fixture
def source(tmp_path, monkeypatch):
    folder = tmp_path / "live"
    folder.mkdir()
    meta = {"live_id": "live1", "status": "completed", "platform": "showroom"}
    metadata = folder / "live1.json"
    metadata.write_text(json.dumps(meta))
    (folder / "live1.mp4").write_bytes(b"video")
    (folder / "live1_yt_thumb.jpg").write_bytes(b"thumbnail")
    config = SimpleNamespace(
        logs_dir=str(tmp_path / "logs"),
        max_concurrent_uploads=1,
        backup_to_gdrive=True,
        youtube_upload_priority_ranks={},
    )
    watcher = Watcher(config)
    upload = AsyncMock(return_value=True)
    recap = AsyncMock()
    youtube = AsyncMock()
    monkeypatch.setattr(module.r2_uploader, "upload", upload)
    monkeypatch.setattr(module.notifier, "send_recap_end_live_notification", recap)
    monkeypatch.setattr(module, "_upload_to_youtube", youtube)
    return SimpleNamespace(
        folder=folder,
        metadata=metadata,
        meta=meta,
        watcher=watcher,
        upload=upload,
        recap=recap,
        youtube=youtube,
        config=config,
    )


@pytest.mark.parametrize("change", ["done", "deleted", "missing_meta", "reconnected"])
def test_queued_r2_rechecks_after_semaphore_admission(source, change):
    r = source

    async def run():
        await r.watcher._r2_semaphore.acquire()
        await r.watcher._scan_queue(str(r.folder.parent))
        await asyncio.sleep(0)
        assert len(r.watcher._tasks) == 1
        if change == "done":
            (r.folder / ".r2_done").write_text("old marker")
        elif change == "deleted":
            shutil.rmtree(r.folder)
        elif change == "missing_meta":
            r.metadata.unlink()
        else:
            r.metadata.write_text(json.dumps({**r.meta, "status": "recording"}))
        tasks = list(r.watcher._tasks)
        r.watcher._r2_semaphore.release()
        await asyncio.wait_for(asyncio.gather(*tasks), 2)

    asyncio.run(run())
    r.upload.assert_not_awaited()
    r.recap.assert_not_awaited()
    r.youtube.assert_not_awaited()
    assert not r.watcher._processing
    if change == "done":
        assert (r.folder / ".r2_done").read_text() == "old marker"
    elif change == "deleted":
        assert not r.folder.exists()


@pytest.mark.parametrize("stage", ["upload", "recap"])
@pytest.mark.parametrize(
    "change", ["missing_meta", "deleted", "reconnected", "done", "invalid_meta"]
)
def test_revalidate_source_after_await(source, stage, change):
    r = source

    async def mutate(*args):
        if change == "missing_meta":
            r.metadata.unlink()
        elif change == "deleted":
            shutil.rmtree(r.folder)
        elif change == "reconnected":
            r.metadata.write_text(json.dumps({**r.meta, "status": "recording"}))
        elif change == "invalid_meta":
            r.metadata.write_text("not json")
        else:
            (r.folder / ".r2_done").write_text("old marker")
        return True

    getattr(r, stage).side_effect = mutate
    r.watcher._processing["live1"] = {}
    asyncio.run(r.watcher._process_folder(str(r.folder), "live1"))
    r.upload.assert_awaited_once()
    if stage == "upload":
        r.recap.assert_not_awaited()
    else:
        r.recap.assert_awaited_once()
    if change == "done":
        assert (r.folder / ".r2_done").read_text() == "old marker"
    else:
        assert not (r.folder / ".r2_done").exists()
    if change == "deleted":
        assert not r.folder.exists()
    r.youtube.assert_not_awaited()


def test_lock_wait_rechecks_source_without_blocking_event_loop(source):
    r = source

    async def run():
        with recording_lock(r.config.logs_dir, "live1"):
            r.watcher._processing["live1"] = {}
            task = asyncio.create_task(
                r.watcher._process_folder(str(r.folder), "live1", is_r2=True)
            )
            await asyncio.sleep(0.02)
            assert not task.done()
            shutil.rmtree(r.folder)
        await asyncio.wait_for(task, 2)

    asyncio.run(run())
    r.upload.assert_not_awaited()
    r.recap.assert_not_awaited()
    assert not r.folder.exists()


def test_shared_lock_protects_upload_and_notifier_from_drive_cleanup(source):
    r = source

    async def run():
        cleanup_entered = asyncio.Event()
        cleanup_started = asyncio.Event()
        cleanup_task = None

        async def cleanup():
            cleanup_started.set()

            # Drive runs this synchronous finalization lock in its worker thread.
            def finalize():
                with recording_lock(r.config.logs_dir, "live1"):
                    assert (r.folder / ".r2_done").exists()
                    shutil.rmtree(r.folder)

            await asyncio.to_thread(finalize)
            cleanup_entered.set()

        async def upload(*args):
            nonlocal cleanup_task
            cleanup_task = asyncio.create_task(cleanup())
            await cleanup_started.wait()
            await asyncio.sleep(0.02)
            assert not cleanup_entered.is_set()
            return True

        async def recap(*args):
            await asyncio.sleep(0.02)
            assert not cleanup_entered.is_set()
            assert r.metadata.exists()
            (r.folder / "live1_web.png").write_bytes(b"recap")

        r.upload.side_effect = upload
        r.recap.side_effect = recap
        r.watcher._processing["live1"] = {}
        await r.watcher._process_folder(str(r.folder), "live1")
        await asyncio.wait_for(cleanup_task, 2)
        assert cleanup_entered.is_set()

    asyncio.run(run())
    assert not r.folder.exists()
    r.recap.assert_awaited_once()


@pytest.mark.parametrize("queued", [False, True])
def test_direct_youtube_does_not_hold_recording_lock(source, queued):
    r = source
    r.config.backup_to_gdrive = False
    r.config.google_client_id = "client"
    r.config.google_client_secret = "secret"
    r.config.youtube_refresh_token = "token"
    r.config.youtube_upload_delay_minutes = 0
    (r.folder / ".r2_done").write_text("done")

    async def run():
        entered = asyncio.Event()
        release = asyncio.Event()

        async def youtube(*args, **kwargs):
            entered.set()
            await release.wait()
            return None, None

        r.youtube.side_effect = youtube
        r.watcher._processing["live1"] = {}
        coroutine = (
            r.watcher._process_with_semaphore(str(r.folder), "live1", False)
            if queued
            else r.watcher._process_folder(str(r.folder), "live1")
        )
        task = asyncio.create_task(coroutine)
        try:
            await asyncio.wait_for(entered.wait(), 2)

            # A recorder reconnect can own the same lock while YouTube waits.
            async def reconnect():
                async with async_recording_lock(r.config.logs_dir, "live1"):
                    assert not task.done()
                    r.metadata.write_text(json.dumps({**r.meta, "status": "recording"}))

            await asyncio.wait_for(reconnect(), 1)
        finally:
            release.set()
            await asyncio.wait_for(task, 2)

    asyncio.run(run())
    r.youtube.assert_awaited_once()
    r.upload.assert_not_awaited()
    r.recap.assert_not_awaited()


def test_reconnect_waits_until_phase_one_finishes(source):
    r = source

    async def run():
        resumed = asyncio.Event()

        async def reconnect():
            async with async_recording_lock(r.config.logs_dir, "live1"):
                assert (r.folder / ".r2_done").exists()
                r.metadata.write_text(json.dumps({**r.meta, "status": "recording"}))
                resumed.set()

        task = None

        async def upload(*args):
            nonlocal task
            task = asyncio.create_task(reconnect())
            await asyncio.sleep(0.02)
            assert not resumed.is_set()
            return True

        r.upload.side_effect = upload
        r.watcher._processing["live1"] = {}
        await r.watcher._process_folder(str(r.folder), "live1")
        await asyncio.wait_for(task, 2)
        assert resumed.is_set()

    asyncio.run(run())
    r.recap.assert_awaited_once()

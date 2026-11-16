"""Offline regressions for direct uploads alongside the Drive controller."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from recorder.src.process_lock import process_lock
from recorder.src.upload import watcher as watcher_module
from recorder.src.upload import youtube_uploader
from recorder.src.upload.watcher import Watcher


@pytest.fixture
def recording(tmp_path):
    meta = {
        "live_id": "live1",
        "status": "completed",
        "platform": "showroom",
        "member_nickname": "Erine",
        "live_type": "public",
    }
    path = tmp_path / "live1.json"
    path.write_text(json.dumps(meta))
    video = tmp_path / "live1.mp4"
    video.write_bytes(b"video")
    (tmp_path / "live1_yt_thumb.jpg").write_bytes(b"thumbnail")
    session = SimpleNamespace(
        live_id="live1",
        live_folder=str(tmp_path),
        json_path=str(path),
        output_path=str(video),
        screenshots_folder=str(tmp_path),
    )
    config = SimpleNamespace(
        logs_dir=str(tmp_path),
        max_concurrent_uploads=1,
        backup_to_gdrive=True,
        gdrive_to_youtube=False,
        google_client_id="client",
        google_client_secret="secret",
        youtube_refresh_token="token",
        youtube_privacy_status="public",
        youtube_upload_delay_minutes=0,
        youtube_upload_priority_ranks={},
    )
    return SimpleNamespace(
        folder=tmp_path, meta=meta, path=path, session=session, config=config
    )


@pytest.mark.parametrize("method", ["_scan_queue", "_scan_direct"])
@pytest.mark.parametrize("master", [False, True])
@pytest.mark.parametrize("subfeature", [False, True])
def test_scans_gate_only_youtube_and_keep_r2_route(
    recording, monkeypatch, method, master, subfeature
):
    r = recording
    r.config.backup_to_gdrive = master
    r.config.gdrive_to_youtube = subfeature
    pending_r2 = r.folder / "r2"
    pending_yt = r.folder / "yt"
    pending_r2.mkdir()
    pending_yt.mkdir()
    (pending_yt / ".r2_done").touch()
    watcher = Watcher(r.config)
    monkeypatch.setattr(
        watcher,
        "_iter_pending",
        lambda _: iter(
            [(r.meta, "r2", str(pending_r2)), (r.meta, "yt", str(pending_yt))]
        ),
    )

    async def run():
        tasks = []
        routed = []
        original_create_task = asyncio.create_task

        async def queue_route(folder, live_id, is_r2):
            routed.append((live_id, is_r2))

        async def direct_route(folder, live_id):
            routed.append((live_id, None))

        def capture(coro):
            task = original_create_task(coro)
            tasks.append(task)
            return task

        monkeypatch.setattr(watcher, "_process_with_semaphore", queue_route)
        monkeypatch.setattr(watcher, "_process_folder", direct_route)
        monkeypatch.setattr(watcher_module.asyncio, "create_task", capture)
        await getattr(watcher, method)(str(r.folder))
        await asyncio.gather(*tasks)
        expected = [("r2", True if method == "_scan_queue" else None)]
        if not master:
            expected.append(("yt", False if method == "_scan_queue" else None))
        assert routed == expected
        assert set(watcher._processing) == ({"r2"} if master else {"r2", "yt"})

    asyncio.run(run())


@pytest.mark.parametrize("r2_done", [False, True])
@pytest.mark.parametrize("subfeature", [False, True])
def test_master_suppresses_phase2_but_preserves_r2(
    recording, monkeypatch, r2_done, subfeature
):
    r = recording
    r.config.gdrive_to_youtube = subfeature
    watcher = Watcher(r.config)
    watcher._processing["live1"] = {}
    monkeypatch.setattr(watcher, "_build_session", lambda *_: (r.meta, r.session))
    upload = AsyncMock(return_value=True)
    recap = AsyncMock()
    youtube = AsyncMock()
    replay = AsyncMock()
    backend = AsyncMock()
    monkeypatch.setattr(watcher_module.r2_uploader, "upload", upload)
    monkeypatch.setattr(watcher_module.r2_uploader, "update_youtube_metadata", backend)
    monkeypatch.setattr(
        watcher_module.notifier, "send_recap_end_live_notification", recap
    )
    monkeypatch.setattr(
        watcher_module.notifier, "send_replay_live_notification", replay
    )
    monkeypatch.setattr(watcher_module, "_upload_to_youtube", youtube)
    history = Mock()
    monkeypatch.setattr(watcher, "_append_history", history)
    if r2_done:
        (r.folder / ".r2_done").touch()
    asyncio.run(watcher._process_folder_inner(str(r.folder), "live1"))
    assert upload.await_count == int(not r2_done)
    assert recap.await_count == int(not r2_done)
    if not r2_done:
        upload.assert_awaited_once_with(
            r.session, r.config, youtube_uploader._format_title(r.meta)
        )
        recap.assert_awaited_once_with("live1", r.config, str(r.folder))
    youtube.assert_not_awaited()
    backend.assert_not_awaited()
    replay.assert_not_awaited()
    history.assert_not_called()
    assert (r.folder / ".r2_done").exists()
    assert not (r.folder / ".yt_done").exists()
    assert (r.folder / "live1.mp4").read_bytes() == b"video"
    assert json.loads(r.path.read_text()) == r.meta


@pytest.fixture
def uploader(recording, monkeypatch):
    upload = Mock(return_value=("new-video", "resume-uri"))
    build = Mock(return_value=object())
    thumbnail = Mock(return_value=True)
    playlist = Mock()
    monkeypatch.setattr(youtube_uploader, "_do_upload_blocking", upload)
    monkeypatch.setattr(youtube_uploader, "_build_youtube", build)
    monkeypatch.setattr(youtube_uploader, "_upload_thumbnail", thumbnail)
    monkeypatch.setattr(youtube_uploader, "_add_to_playlist_blocking", playlist)
    return SimpleNamespace(
        upload=upload, build=build, thumbnail=thumbnail, playlist=playlist
    )


@pytest.mark.parametrize("failure", ["build", "thumbnail"])
def test_callback_checkpoints_before_thumbnail_failure(recording, uploader, failure):
    r = recording
    events = []
    title = youtube_uploader._format_title(r.meta)

    async def checkpoint(video_id, video_title):
        assert (video_id, video_title) == ("new-video", title)
        assert json.loads(r.path.read_text())["youtube_id"] == "new-video"
        events.append("checkpoint")

    def fail(*args):
        assert events == ["checkpoint"]
        events.append("thumbnail-failure")
        raise RuntimeError("thumbnail API failure")

    getattr(uploader, failure).side_effect = fail
    with pytest.raises(RuntimeError, match="thumbnail API failure"):
        asyncio.run(
            youtube_uploader._upload_to_youtube(
                r.session, r.config, on_video_uploaded=checkpoint
            )
        )
    assert events == ["checkpoint", "thumbnail-failure"]
    assert json.loads(r.path.read_text())["youtube_title"] == title
    uploader.upload.assert_called_once()
    uploader.playlist.assert_not_called()


@pytest.mark.parametrize("fail_thumbnail", [False, True])
def test_no_hook_preserves_legacy_metadata_order_and_result(
    recording, uploader, fail_thumbnail
):
    r = recording

    def thumbnail(*args):
        assert json.loads(r.path.read_text()) == r.meta
        if fail_thumbnail:
            raise RuntimeError("thumbnail failed")
        return True

    uploader.thumbnail.side_effect = thumbnail
    if fail_thumbnail:
        with pytest.raises(RuntimeError, match="thumbnail failed"):
            asyncio.run(youtube_uploader._upload_to_youtube(r.session, r.config))
        assert json.loads(r.path.read_text()) == r.meta
        uploader.playlist.assert_not_called()
    else:
        assert asyncio.run(
            youtube_uploader._upload_to_youtube(r.session, r.config)
        ) == ("new-video", "resume-uri")
        assert json.loads(r.path.read_text())["youtube_id"] == "new-video"
        uploader.playlist.assert_called_once()
    uploader.upload.assert_called_once()


@pytest.mark.parametrize("with_hook", [False, True])
def test_existing_youtube_id_skips_upload_and_optional_hooks(
    recording, uploader, with_hook
):
    r = recording
    r.meta["youtube_id"] = "existing-video"
    r.path.write_text(json.dumps(r.meta))
    before = r.path.read_bytes()
    hook = AsyncMock()
    kwargs = {"on_video_uploaded": hook} if with_hook else {}
    assert asyncio.run(
        youtube_uploader._upload_to_youtube(r.session, r.config, **kwargs)
    ) == ("existing-video", None)
    hook.assert_not_awaited()
    for mock in (
        uploader.upload,
        uploader.build,
        uploader.thumbnail,
        uploader.playlist,
    ):
        mock.assert_not_called()
    assert r.path.read_bytes() == before


@pytest.mark.parametrize("is_r2", [False, True])
def test_shutdown_drains_active_work_holds_lock_and_skips_semaphore_waiters(
    recording, monkeypatch, is_r2
):
    r = recording
    r.config.poll_interval = 15
    watcher = Watcher(r.config)

    async def run():
        stop = asyncio.Event()
        entered = asyncio.Event()
        release = asyncio.Event()
        shutting_down = asyncio.Event()
        calls = []

        async def process(folder, live_id):
            calls.append(live_id)
            entered.set()
            await release.wait()

        async def controller(event):
            assert event is stop
            for live_id in ("active", "waiting"):
                watcher._processing[live_id] = {}
                watcher._spawn(
                    watcher._process_with_semaphore(str(r.folder), live_id, is_r2)
                )
            await event.wait()
            # run's finally executes without yielding before it starts draining.
            shutting_down.set()

        monkeypatch.setattr(watcher, "_process_folder_inner", process)
        monkeypatch.setattr(watcher, "_run", controller)
        task = asyncio.create_task(watcher.run(stop))
        try:
            await asyncio.wait_for(entered.wait(), 2)
            assert len(watcher._tasks) == 2
            assert calls == ["active"]
            stop.set()
            await asyncio.wait_for(shutting_down.wait(), 2)
            assert watcher._stopping
            assert not task.done()
            assert calls == ["active"]
            with pytest.raises(RuntimeError, match="Another upload controller"):
                with process_lock(r.config.logs_dir, "upload"):
                    pytest.fail("Upload lock released before active work finished")
        finally:
            stop.set()
            release.set()
            await asyncio.wait_for(task, 2)
        assert calls == ["active"], "Semaphore waiter must not begin after shutdown"
        assert not watcher._processing
        assert not watcher._tasks
        semaphore = watcher._r2_semaphore if is_r2 else watcher._yt_semaphore
        assert semaphore._value == 1
        with process_lock(r.config.logs_dir, "upload"):
            pass

    asyncio.run(run())


def test_direct_pipeline_without_drive_completes_r2_then_youtube(
    recording, monkeypatch
):
    r = recording
    r.config.backup_to_gdrive = False
    watcher = Watcher(r.config)
    monkeypatch.setattr(watcher, "_build_session", lambda *_: (r.meta, r.session))
    events = []

    async def r2(*args):
        events.append("r2")
        return True

    async def recap(*args):
        events.append("recap")

    async def youtube(*args, **kwargs):
        assert (r.folder / ".r2_done").exists()
        assert "on_video_uploaded" not in kwargs
        events.append("youtube")
        return "video-id", "resume-uri"

    async def backend(*args):
        events.append("backend")
        return True

    async def replay(*args):
        events.append("replay")

    upload = AsyncMock(side_effect=r2)
    yt = AsyncMock(side_effect=youtube)
    update = AsyncMock(side_effect=backend)
    notification = AsyncMock(side_effect=replay)
    history = Mock()
    monkeypatch.setattr(watcher_module.r2_uploader, "upload", upload)
    monkeypatch.setattr(
        watcher_module.notifier,
        "send_recap_end_live_notification",
        AsyncMock(side_effect=recap),
    )
    monkeypatch.setattr(watcher_module, "_upload_to_youtube", yt)
    monkeypatch.setattr(watcher_module.r2_uploader, "update_youtube_metadata", update)
    monkeypatch.setattr(
        watcher_module.notifier, "send_replay_live_notification", notification
    )
    monkeypatch.setattr(watcher, "_append_history", history)

    async def run():
        for phase in range(2):
            watcher._processing["live1"] = {}
            await watcher._process_folder(str(r.folder), "live1")
            assert not watcher._processing
            if phase == 0:
                yt.assert_not_awaited()
                assert not (r.folder / ".yt_done").exists()

    asyncio.run(run())
    assert events == ["r2", "recap", "youtube", "backend", "replay"]
    upload.assert_awaited_once()
    yt.assert_awaited_once()
    update.assert_awaited_once_with(
        "live1",
        "video-id",
        youtube_uploader._format_title(r.meta),
        r.config,
        watcher.log_upl,
    )
    notification.assert_awaited_once_with(
        "live1",
        youtube_uploader._format_title(r.meta),
        "video-id",
        r.config,
        str(r.folder),
    )
    history.assert_called_once_with("live1", "video-id")
    assert (r.folder / ".r2_done").exists()
    assert (r.folder / ".yt_done").exists()
    assert not watcher._stopping

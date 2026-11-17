"""Service contracts with real durable state and explicitly metered API attempts."""

import asyncio
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from recorder.src.ytpublic.client import APIRequestError, AuthorizationError
from recorder.src.ytpublic.service import StopRequested, YTPublicService
from recorder.src.ytpublic.state import (
    DailyLimitError,
    PublicationState,
    SpacingError,
    StateError,
)

CHANNEL = "UC0123456789abcdefghijkl"
PLAYLIST = "UU0123456789abcdefghijkl"
START = datetime(2026, 1, 5, tzinfo=timezone.utc).timestamp()
IDN_TITLE = "Live IDN Freya JKT48 | Senin, 5 Januari 2026 07:00 WIB"


def video(index=0, title="Live SHOWROOM Freya JKT48", privacy="private"):
    return {
        "id": f"vid{index:08d}",
        "snippet": {
            "channelId": CHANNEL,
            "title": title,
            "publishedAt": "2026-01-05T00:00:00Z",
        },
        "status": {"privacyStatus": privacy},
    }


class MeteredClient:
    def __init__(self, state, videos):
        self.state = state
        self.videos = {item["id"]: deepcopy(item) for item in videos}
        self.ids = list(self.videos)
        self.calls = []
        self.updates = []
        self.checkpoints = []
        self.closed = False
        self.before_read = None
        self.update_result = "confirmed"
        self.authorization_error = False
        self.repeated_token = False

    def _read(self, name, *args):
        self.state.reserve(1)
        self.calls.append((name, *args))
        if self.authorization_error:
            raise AuthorizationError("credentials rejected")

    def discover_channel(self):
        self._read("discover")
        return {"channel_id": CHANNEL, "playlist_id": PLAYLIST}

    def list_upload_page(self, playlist_id, page_token=None):
        assert playlist_id == PLAYLIST
        self._read("page", page_token)
        start = int(page_token or 0)
        ids = self.ids[start : start + 50]
        token = str(start + 50) if start + 50 < len(self.ids) else None
        if self.repeated_token:
            token = "50"
        return {"ids": ids, "next_page_token": token}

    def get_videos(self, ids):
        assert 0 < len(ids) <= 50
        self._read("videos", tuple(ids))
        if self.before_read:
            self.before_read(self, ids)
        return deepcopy([self.videos[key] for key in ids if key in self.videos])

    def make_public(self, resource, before_update):
        self.state.reserve(50, update=True)
        before_update()
        key = resource["id"]
        assert resource["snippet"]["channelId"] == CHANNEL
        assert resource["status"]["privacyStatus"] == "private"
        receipt = self.state.read_receipt(key)
        assert receipt["status"] == "publishing"
        self.checkpoints.append(deepcopy(receipt))
        self.calls.append(("update", key))
        self.updates.append(key)
        if self.update_result != "lost_private":
            self.videos[key]["status"]["privacyStatus"] = "public"
        if self.update_result.startswith("lost"):
            raise APIRequestError("response lost")
        if self.update_result == "unconfirmed":
            return {"id": key, "status": {}}
        return deepcopy(self.videos[key])

    def close(self):
        self.closed = True


@pytest.fixture
def harness(tmp_path):
    def build(videos=(), *, now=START, **overrides):
        config = SimpleNamespace(
            logs_dir=str(tmp_path),
            ytpublic_enabled=True,
            ytpublic_dry_run=False,
            ytpublic_poll_interval=900,
            ytpublic_base_delay_hours=72,
            ytpublic_buffer_hours=8,
            ytpublic_excluded_video_ids=set(),
            ytpublic_max_updates_per_day=80,
            ytpublic_max_updates_per_scan=5,
            ytpublic_update_interval_seconds=0,
            ytpublic_daily_quota_budget=5000,
        )
        for name, value in overrides.items():
            setattr(config, name, value)

        def clock():
            return now
        state = PublicationState(config, clock=clock)
        client = MeteredClient(state, videos)
        service = YTPublicService(config, client=client, state=state, clock=clock)
        return service, client, state

    return build


async def scan(service):
    try:
        await service.scan_once()
    finally:
        await service.close()


def restart(service, client):
    state = PublicationState(service.config, clock=service.clock)
    client.state = state
    return (
        YTPublicService(
            service.config, client=client, state=state, clock=service.clock
        ),
        state,
    )


@pytest.mark.parametrize("enabled", [False, True])
def test_enabled_disabled(harness, enabled):
    service, client, state = harness([video()], ytpublic_enabled=enabled)
    asyncio.run(scan(service))
    if enabled:
        assert client.updates == [video()["id"]]
        assert state.status()["used_units"] == 54
        assert client.closed
    else:
        assert client.calls == []
        assert state.status()["used_units"] == 0
        assert state.read_receipt(video()["id"]) is None


def test_dry_run_has_no_update_or_receipt(harness, caplog):
    service, client, state = harness([video()], ytpublic_dry_run=True)
    with caplog.at_level("INFO", logger="ytpublic"):
        asyncio.run(scan(service))
    assert "DRY-RUN" in caplog.text
    assert client.updates == []
    assert state.read_receipt(video()["id"]) is None
    assert state.status()["update_attempts"] == 0
    assert state.status()["used_units"] == 3


@pytest.mark.parametrize("hours,expected", [(79.999, False), (80, True)])
def test_idn_eighty_hour_boundary_and_showroom_immediate(harness, hours, expected):
    service, client, state = harness(
        [video(0), video(1, IDN_TITLE)], now=START + hours * 3600
    )
    asyncio.run(scan(service))
    assert (video(1)["id"] in client.updates) is expected
    assert video(0)["id"] in client.updates
    if expected:
        receipt = state.read_receipt(video(1)["id"])
        assert receipt["matched_rule"] == "idn_delayed"
        assert receipt["eligible_at"] == "2026-01-08T08:00:00+00:00"


@pytest.mark.parametrize(
    "resource",
    [video(title="Live IDN JKT48 Official"), video(privacy="unlisted")],
)
def test_official_and_unlisted_are_skipped(harness, resource):
    service, client, state = harness([resource], now=START + 100 * 3600)
    asyncio.run(scan(service))
    assert client.updates == []
    assert state.read_receipt(resource["id"]) is None


@pytest.mark.parametrize("change", ["privacy", "title", "missing"])
def test_fresh_read_respects_manual_changes(harness, change):
    resource = video()
    service, client, state = harness([resource])
    reads = 0

    def mutate(fake, ids):
        nonlocal reads
        reads += 1
        if reads == 2:
            assert ids == [resource["id"]]
            if change == "privacy":
                fake.videos[resource["id"]]["status"]["privacyStatus"] = "unlisted"
            elif change == "title":
                fake.videos[resource["id"]]["snippet"]["title"] = "Personal archive"
            else:
                del fake.videos[resource["id"]]

    client.before_read = mutate
    asyncio.run(scan(service))
    assert reads == 2
    assert client.updates == []
    assert state.read_receipt(resource["id"]) is None


def test_at_most_five_updates_per_scan(harness):
    service, client, state = harness([video(i) for i in range(8)])
    asyncio.run(scan(service))
    assert len(client.updates) == 5
    assert state.status()["update_attempts"] == 5
    assert len(client.checkpoints) == 5


def test_eighty_daily_attempts_survive_restart(harness):
    service, client, state = harness([video()])
    for _ in range(79):
        state.reserve(50, update=True)
    asyncio.run(scan(service))
    assert state.status()["update_attempts"] == 80
    service, state = restart(service, client)
    calls = list(client.calls)
    with pytest.raises(DailyLimitError) as error:
        asyncio.run(scan(service))
    assert error.value.kind == "update_attempts"
    assert client.calls == calls
    assert len(client.updates) == 1


@pytest.mark.parametrize("budget,units", [(1, 1), (3, 3), (53, 4)])
def test_read_costs_gate_discovery_fresh_read_and_update(harness, budget, units):
    service, client, state = harness([video()], ytpublic_daily_quota_budget=budget)
    with pytest.raises(DailyLimitError) as error:
        asyncio.run(scan(service))
    assert error.value.kind == "quota_budget"
    assert state.status()["used_units"] == units
    assert state.status()["update_attempts"] == 0
    assert client.updates == []
    assert state.read_receipt(video()["id"]) is None


def test_exhausted_budget_blocks_all_reads_after_restart(harness):
    service, client, state = harness([video()], ytpublic_daily_quota_budget=54)
    asyncio.run(scan(service))
    service, state = restart(service, client)
    calls = list(client.calls)
    with pytest.raises(DailyLimitError):
        asyncio.run(scan(service))
    assert client.calls == calls
    assert state.status()["used_units"] == 54


def test_receipt_prevents_republication_after_manual_privacy_change(harness):
    service, client, state = harness([video()])
    asyncio.run(scan(service))
    original = state.read_receipt(video()["id"])
    assert original["status"] == "published"
    client.videos[video()["id"]]["status"]["privacyStatus"] = "private"
    service, state = restart(service, client)
    asyncio.run(scan(service))
    assert client.updates == [video()["id"]]
    assert state.read_receipt(video()["id"]) == original


@pytest.mark.parametrize(
    "outcome,expected",
    [
        ("lost_public", "published"),
        ("lost_private", "needs_reconciliation"),
        ("unconfirmed", "published"),
    ],
)
def test_ambiguous_update_is_checkpointed_and_reconciled_without_retry(
    harness, outcome, expected
):
    service, client, state = harness([video()])
    client.update_result = outcome
    if outcome.startswith("lost"):
        with pytest.raises(APIRequestError, match="response lost"):
            asyncio.run(scan(service))
    else:
        asyncio.run(scan(service))
    assert state.read_receipt(video()["id"])["status"] == "needs_reconciliation"
    assert client.checkpoints[0]["status"] == "publishing"
    service, state = restart(service, client)
    asyncio.run(scan(service))
    assert state.read_receipt(video()["id"])["status"] == expected
    asyncio.run(scan(service))
    assert client.updates == [video()["id"]]
    assert state.status()["update_attempts"] == 1


def test_large_backlog_resumes_persisted_pagination_after_restart(harness):
    resources = [video(i, title="Archive") for i in range(251)]
    service, client, state = harness(resources, ytpublic_daily_quota_budget=5)
    with pytest.raises(DailyLimitError):
        asyncio.run(scan(service))
    catalog = state.load_catalog()
    assert catalog["page_token"] == "100"
    assert not catalog["full_scan_complete"]
    assert len(catalog["known_ids"]) == 100
    service.config.ytpublic_daily_quota_budget = 100
    service, state = restart(service, client)
    client.calls.clear()
    asyncio.run(scan(service))
    assert next(call for call in client.calls if call[0] == "page") == ("page", "100")
    catalog = state.load_catalog()
    assert catalog["full_scan_complete"]
    assert set(catalog["videos"]) == set(client.ids)
    assert set(catalog["known_ids"]) == set(client.ids)
    assert catalog["page_token"] is None


def test_completed_catalog_reads_head_and_rotates_cached_status_batches(harness):
    service, client, state = harness([video(i, title="Archive") for i in range(121)])
    asyncio.run(scan(service))
    service, state = restart(service, client)
    new = video(999, title="Archive")
    client.videos[new["id"]] = new
    client.ids.insert(0, new["id"])
    client.calls.clear()
    asyncio.run(scan(service))
    assert [call for call in client.calls if call[0] == "page"] == [("page", None)]
    batches = [call[1] for call in client.calls if call[0] == "videos"]
    assert batches[0] == (new["id"],)
    known = state.load_catalog()["known_ids"]
    assert batches[1] == tuple(known[:50])
    assert state.load_catalog()["refresh_cursor"] == 50
    client.calls.clear()
    asyncio.run(scan(service))
    assert [call[1] for call in client.calls if call[0] == "videos"] == [
        tuple(known[50:100])
    ]
    assert state.load_catalog()["refresh_cursor"] == 100


def test_repeated_pagination_token_fails_closed(harness):
    service, client, state = harness([video(i) for i in range(101)])
    client.repeated_token = True
    with pytest.raises(StateError, match="Repeated.*pagination token"):
        asyncio.run(scan(service))
    assert client.updates == []
    assert state.status()["update_attempts"] == 0
    assert not state.load_catalog()["full_scan_complete"]


def test_run_authorization_pause_stays_alive_until_stop(harness, caplog):
    service, client, state = harness([video()])
    client.authorization_error = True

    async def exercise():
        stop = asyncio.Event()
        task = asyncio.create_task(service.run(stop))
        try:

            async def paused():
                while not service._paused:
                    await asyncio.sleep(0)

            await asyncio.wait_for(paused(), timeout=2)
            calls = list(client.calls)
            await asyncio.sleep(0.01)
            assert not task.done()
            assert client.calls == calls == [("discover",)]
        finally:
            stop.set()
            await asyncio.wait_for(task, timeout=2)

    with caplog.at_level("CRITICAL", logger="ytpublic"):
        asyncio.run(exercise())
    assert "authorization invalid" in caplog.text
    assert client.closed
    assert state.status()["update_attempts"] == 0


def test_stop_during_spacing_prevents_update(harness):
    service, client, state = harness([video()], ytpublic_update_interval_seconds=86400)
    state.reserve(50, update=True)

    async def exercise():
        stop = asyncio.Event()
        service.stop_event = stop
        task = asyncio.create_task(service.scan_once())
        try:

            async def discovered():
                while not state.load_catalog().get("full_scan_complete"):
                    await asyncio.sleep(0)

            await asyncio.wait_for(discovered(), timeout=2)
            await asyncio.sleep(0.01)
            assert not task.done()
            stop.set()
            with pytest.raises(StopRequested):
                await asyncio.wait_for(task, timeout=2)
        finally:
            stop.set()
            if not task.done():
                await asyncio.gather(task, return_exceptions=True)
            await service.close()

    asyncio.run(exercise())
    assert client.updates == []
    assert state.status()["update_attempts"] == 1
    assert state.read_receipt(video()["id"]) is None
    assert client.closed


@pytest.mark.parametrize("privacy", ["public", "private"])
@pytest.mark.parametrize("status", ["publishing", "needs_reconciliation"])
def test_dry_run_preserves_pending_receipts(harness, monkeypatch, privacy, status):
    resource = video(privacy=privacy)
    service, client, state = harness([resource], ytpublic_dry_run=True)
    receipt = {
        "schema_version": 1,
        "video_id": resource["id"],
        "channel_id": CHANNEL,
        "status": status,
        "attempted_at": "2026-01-05T00:00:00+00:00",
        "published_at": None,
    }
    state.write_receipt(resource["id"], receipt)
    path = state.receipts / f"{resource['id']}.json"
    original = path.read_bytes()

    def forbidden_write(*args, **kwargs):
        pytest.fail("dry-run must not write a receipt")

    monkeypatch.setattr(state, "write_receipt", forbidden_write)
    asyncio.run(scan(service))
    assert state.read_receipt(resource["id"]) == receipt
    assert path.read_bytes() == original
    assert client.calls == [
        ("discover",),
        ("page", None),
        ("videos", (resource["id"],)),
    ]
    assert client.updates == []
    assert state.status()["update_attempts"] == 0
    assert client.closed


def test_invalid_exclusions_fail_closed_before_api_access(harness):
    service, client, state = harness([video()])

    class InvalidExclusions(SimpleNamespace):
        @property
        def ytpublic_excluded_video_ids(self):
            raise ValueError("invalid video ID")

    fields = vars(service.config).copy()
    del fields["ytpublic_excluded_video_ids"]
    service.config = InvalidExclusions(**fields)
    with pytest.raises(
        StateError, match="Invalid ytpublic exclusion configuration"
    ) as error:
        asyncio.run(scan(service))
    assert isinstance(error.value.__cause__, ValueError)
    assert client.calls == []
    assert state.status()["used_units"] == 0
    assert state.read_receipt(video()["id"]) is None


def test_run_spacing_error_waits_until_deadline_without_pausing(harness, monkeypatch):
    service, client, state = harness([video()])
    deadline = START + 3600
    scans = 0

    async def spacing_conflict():
        nonlocal scans
        scans += 1
        raise SpacingError(deadline)

    monkeypatch.setattr(service, "scan_once", spacing_conflict)

    async def exercise():
        stop = asyncio.Event()
        task = asyncio.create_task(service.run(stop))
        try:

            async def handled():
                while (
                    not task.done() and not service._retry_after and not service._paused
                ):
                    await asyncio.sleep(0)

            await asyncio.wait_for(handled(), timeout=2)
            assert not task.done()
            assert not service._paused
            assert service._retry_after == deadline
            await asyncio.sleep(0.01)
            assert scans == 1
            assert not task.done()
        finally:
            stop.set()
            await asyncio.wait_for(task, timeout=2)

    asyncio.run(exercise())
    assert client.calls == []
    assert state.status()["update_attempts"] == 0

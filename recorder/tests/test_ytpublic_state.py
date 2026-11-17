import json
import os
import stat
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from recorder.src.ytpublic.state import (
    DailyLimitError,
    PublicationState,
    SpacingError,
    StateError,
)

VIDEO = "abcdefgh_-1"
PT = ZoneInfo("America/Los_Angeles")


@pytest.fixture
def setup_state(tmp_path):
    config = SimpleNamespace(logs_dir=tmp_path)
    now = [datetime(2026, 1, 10, 12, tzinfo=PT).timestamp()]

    def restart():
        return PublicationState(config, clock=lambda: now[0])

    return config, now, restart


def test_default_attempt_limit_counts_failed_calls_and_survives_restart(setup_state):
    _, now, restart = setup_state
    for _ in range(80):
        state = restart()
        state.reserve(50, update=True)
        # Simulate a failed/ambiguous network call: no success callback or refund.
        now[0] += 30
    state = restart()
    assert state.status()["update_attempts"] == 80
    assert state.status()["used_units"] == 4000
    with pytest.raises(DailyLimitError) as error:
        state.reserve(50, update=True)
    assert error.value.kind == "update_attempts"
    assert error.value.reset_at == state.status()["reset_at"]
    state.reserve(1)  # Attempt cap does not forbid reconciliation reads.


def test_reads_share_budget_and_rejected_reservations_do_not_charge(setup_state):
    _, _, restart = setup_state
    state = restart()
    state.reserve(4949)
    state.reserve(50, update=True)
    state.reserve(1)
    before = state.status()
    with pytest.raises(DailyLimitError) as error:
        restart().reserve(1)
    assert error.value.kind == "quota_budget"
    assert restart().status() == before


def test_spacing_survives_restart_and_midnight(setup_state):
    _, now, restart = setup_state
    now[0] = datetime(2026, 1, 10, 23, 59, 50, tzinfo=PT).timestamp()
    restart().reserve(50, update=True)
    deadline = now[0] + 30
    now[0] += 10
    state = restart()
    status = state.status()
    assert status["quota_day"] == "2026-01-11"
    assert status["update_attempts"] == status["used_units"] == 0
    assert status["next_update_at"] == deadline
    with pytest.raises(SpacingError) as error:
        state.reserve(50, update=True)
    assert error.value.deadline == deadline
    state.reserve(1)
    now[0] = deadline
    restart().reserve(50, update=True)
    assert restart().status()["used_units"] == 51


def test_quota_pause_is_durable_and_resets_at_midnight(setup_state):
    _, now, restart = setup_state
    state = restart()
    state.reserve(1)
    state.mark_quota_exhausted()
    reset = state.status()["reset_at"]
    assert restart().status()["quota_pause_until"] == reset
    for update in (False, True):
        with pytest.raises(DailyLimitError) as error:
            restart().reserve(50 if update else 1, update=update)
        assert error.value.kind == "quota_pause"
        assert error.value.reset_at == reset
    now[0] = reset
    restart().reserve(1)
    assert restart().status()["quota_pause_until"] == 0
    assert restart().status()["used_units"] == 1


@pytest.mark.parametrize("month,day,hours", [(3, 8, 23), (11, 1, 25)])
def test_pacific_dst_calendar_days(setup_state, month, day, hours):
    _, now, restart = setup_state
    now[0] = datetime(2026, month, day, tzinfo=PT).timestamp()
    state = restart()
    state.reserve(1)
    reset = state.status()["reset_at"]
    assert reset - now[0] == hours * 3600
    now[0] = reset - 0.001
    assert restart().status()["used_units"] == 1
    now[0] = reset
    assert restart().status()["used_units"] == 0


@pytest.mark.parametrize(
    "contents",
    [
        "{",
        "null",
        "[]",
        "{}",
        '{"schema_version":1,"schema_version":1}',
    ],
)
def test_corrupt_ledger_fails_closed_without_overwriting(setup_state, contents):
    _, now, restart = setup_state
    state = restart()
    state.status()
    path = state.root / "quota.json"
    path.write_text(contents)
    now[0] += 3 * 86400
    for operation in (
        state.status,
        lambda: state.reserve(1),
        state.mark_quota_exhausted,
    ):
        with pytest.raises(StateError):
            operation()
        assert path.read_text() == contents


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema_version", True),
        ("schema_version", 2),
        ("quota_day", "2026-99-99"),
        ("quota_day", "2099-01-01"),
        ("update_attempts", -1),
        ("used_units", True),
        ("next_update_at", float("nan")),
        ("quota_pause_until", "0"),
    ],
)
def test_invalid_ledger_fields_fail_closed(setup_state, key, value):
    _, _, restart = setup_state
    state = restart()
    ledger = state.status()
    ledger.pop("reset_at")
    ledger[key] = value
    (state.root / "quota.json").write_text(json.dumps(ledger))
    with pytest.raises(StateError):
        restart().reserve(1)


@pytest.mark.parametrize(
    "video_id", ["../secrets!", "a/bcdefghij", "", "a" * 12, "é" * 11, None]
)
def test_no_hostile_video_paths(setup_state, video_id):
    _, _, restart = setup_state
    state = restart()
    for operation in (
        lambda: state.read_receipt(video_id),
        lambda: state.write_receipt(video_id, {}),
        lambda: state.save_catalog({"videos": {video_id: {}}}),
    ):
        with pytest.raises(StateError):
            operation()
    assert list(state.receipts.iterdir()) == []


@pytest.mark.parametrize("status", ["publishing", "published", "needs_reconciliation"])
def test_receipts_round_trip_and_permissions(setup_state, status):
    _, _, restart = setup_state
    state = restart()
    assert state.read_receipt(VIDEO) is None
    value = {
        "schema_version": 1,
        "video_id": VIDEO,
        "status": status,
        "observed_title": "Live",
    }
    state.write_receipt(VIDEO, value)
    assert restart().read_receipt(VIDEO) == value
    assert stat.S_IMODE(state.root.stat().st_mode) == 0o700
    assert stat.S_IMODE(state.receipts.stat().st_mode) == 0o700
    for path in (state.receipts / f"{VIDEO}.json", state.root / ".lock"):
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


@pytest.mark.parametrize(
    "patch",
    [
        {"schema_version": True},
        {"schema_version": 2},
        {"video_id": "12345678901"},
        {"status": "failed"},
    ],
)
def test_invalid_receipts_are_rejected_on_read_and_write(setup_state, patch):
    _, _, restart = setup_state
    state = restart()
    value = {"schema_version": 1, "video_id": VIDEO, "status": "publishing", **patch}
    with pytest.raises(StateError):
        state.write_receipt(VIDEO, value)
    (state.receipts / f"{VIDEO}.json").write_text(json.dumps(value))
    with pytest.raises(StateError):
        state.read_receipt(VIDEO)


def test_receipt_atomic_replace_failure_retains_previous_value(
    setup_state, monkeypatch
):
    _, _, restart = setup_state
    state = restart()
    original = {"schema_version": 1, "video_id": VIDEO, "status": "publishing"}
    state.write_receipt(VIDEO, original)

    def fail_replace(source, destination):
        assert json.loads(open(source).read())["status"] == "published"
        raise OSError("simulated replacement failure")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(StateError):
        state.write_receipt(VIDEO, {**original, "status": "published"})
    assert state.read_receipt(VIDEO) == original
    assert sorted(path.name for path in state.receipts.iterdir()) == [f"{VIDEO}.json"]


def test_catalog_exact_round_trip_and_validation(setup_state):
    _, _, restart = setup_state
    state = restart()
    assert state.load_catalog() == {}
    value = {
        "schema_version": "service-owned",
        "channels": [{"id": "channel"}],
        "playlists": {"uploads": "playlist"},
        "videos": {VIDEO: {"status": {"privacyStatus": "private"}}},
        "discovery_cursor": {"page_token": "next", "complete": False},
    }
    state.save_catalog(value)
    assert restart().load_catalog() == value
    assert stat.S_IMODE((state.root / "catalog.json").stat().st_mode) == 0o600
    for invalid in ([], {"videos": []}, {"x": float("inf")}, {"x": object()}):
        with pytest.raises(StateError):
            state.save_catalog(invalid)
    (state.root / "catalog.json").write_text('{"schema_version":2,"data":{}}')
    with pytest.raises(StateError):
        state.load_catalog()


def test_symlink_state_is_not_followed(setup_state, tmp_path):
    _, _, restart = setup_state
    state = restart()
    outside = tmp_path / "outside.json"
    outside.write_text("{}")
    (state.root / "quota.json").symlink_to(outside)
    with pytest.raises(StateError):
        state.reserve(1)
    assert outside.read_text() == "{}"


def test_separate_instances_serialize_reservations(setup_state):
    config, _, restart = setup_state
    config.ytpublic_daily_quota_budget = 10
    states = [restart() for _ in range(20)]

    def reserve(state):
        try:
            state.reserve(1)
            return True
        except DailyLimitError:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(reserve, states)) == 10
    assert restart().status()["used_units"] == 10


@pytest.mark.parametrize("cost", [0, -1, True, 1.5, "50"])
def test_invalid_cost_does_not_create_ledger(setup_state, cost):
    _, _, restart = setup_state
    state = restart()
    with pytest.raises(StateError):
        state.reserve(cost, update=True)
    assert not (state.root / "quota.json").exists()

"""Durable, worker-local publication receipts and conservative quota accounting."""

import fcntl
import json
import math
import os
import re
import stat
import tempfile
import threading
import time
from contextlib import contextmanager
from datetime import date, datetime
from datetime import time as day_time
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")
VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}", re.ASCII)


class StateError(RuntimeError):
    """State is invalid or could not be durably accessed."""


class DailyLimitError(StateError):
    def __init__(self, kind, reset_at: float):
        self.kind = kind
        self.reset_at = reset_at
        super().__init__(f"{kind} until {reset_at}")


class SpacingError(StateError):
    def __init__(self, deadline: float):
        self.deadline = deadline
        super().__init__(f"Update spacing until {deadline}")


def _video_id(value):
    if not isinstance(value, str) or VIDEO_ID.fullmatch(value) is None:
        raise StateError("Invalid YouTube video ID")


def _number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def _mapping(value):
    if not isinstance(value, dict):
        raise StateError("Expected a JSON mapping")

    # Round-trip also rejects NaN, non-JSON values, and non-string mapping keys.
    def keys(item):
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise StateError("JSON mapping keys must be strings")
            for child in item.values():
                keys(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                keys(child)

    keys(value)
    try:
        return json.loads(json.dumps(value, allow_nan=False))
    except (TypeError, ValueError, OverflowError) as exc:
        raise StateError("Invalid JSON value") from exc


class PublicationState:
    def __init__(self, config, clock=None):
        self.clock = clock if clock is not None else time.time
        self.max_updates = getattr(config, "ytpublic_max_updates_per_day", 80)
        self.budget = getattr(config, "ytpublic_daily_quota_budget", 5000)
        self.interval = getattr(config, "ytpublic_update_interval_seconds", 30)
        if (
            type(self.max_updates) is not int
            or self.max_updates <= 0
            or type(self.budget) is not int
            or self.budget <= 0
            or not _number(self.interval)
        ):
            raise StateError("Invalid quota configuration")
        self.root = Path(config.logs_dir) / "ytpublic"
        self.receipts = self.root / "receipts"
        self._mutex = threading.RLock()
        try:
            for directory in (self.root, self.receipts):
                directory.mkdir(mode=0o700, parents=True, exist_ok=True)
                if directory.is_symlink() or not directory.is_dir():
                    raise StateError("Unsafe state directory")
                directory.chmod(0o700)
        except OSError as exc:
            raise StateError("Cannot initialize publication state") from exc

    @contextmanager
    def _locked(self):
        with self._mutex:
            try:
                fd = os.open(
                    self.root / ".lock",
                    os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW,
                    0o600,
                )
                with os.fdopen(fd, "a+") as lock:
                    os.fchmod(lock.fileno(), 0o600)
                    fcntl.flock(lock, fcntl.LOCK_EX)
                    try:
                        yield
                    finally:
                        fcntl.flock(lock, fcntl.LOCK_UN)
            except OSError as exc:
                raise StateError("Publication state I/O failed") from exc

    def _read(self, path):
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        except FileNotFoundError:
            return None
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise StateError("State must be a regular file")
            os.fchmod(stream.fileno(), 0o600)
            try:

                def pairs(items):
                    result = {}
                    for key, value in items:
                        if key in result:
                            raise StateError("Duplicate JSON key")
                        result[key] = value
                    return result

                value = json.load(stream, object_pairs_hook=pairs)
            except (ValueError, UnicodeError) as exc:
                raise StateError(f"Corrupt state: {path.name}") from exc
        return _mapping(value)

    def _write(self, path, value):
        value = _mapping(value)
        temporary = None
        try:
            fd, temporary = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                os.fchmod(stream.fileno(), 0o600)
                json.dump(value, stream, allow_nan=False, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            temporary = None
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if temporary is not None:
                os.unlink(temporary)

    def _ledger(self):
        now = self.clock()
        if not _number(now):
            raise StateError("Invalid clock")
        today = datetime.fromtimestamp(now, PACIFIC).date()
        reset = datetime.combine(today + timedelta(days=1), day_time(), PACIFIC)
        reset_at = reset.timestamp()
        path = self.root / "quota.json"
        ledger = self._read(path)
        if ledger is None:
            ledger = {
                "schema_version": 1,
                "quota_day": today.isoformat(),
                "update_attempts": 0,
                "used_units": 0,
                "next_update_at": 0.0,
                "quota_pause_until": 0.0,
            }
            self._write(path, ledger)
        else:
            try:
                quota_day = date.fromisoformat(ledger["quota_day"])
                valid = (
                    type(ledger["schema_version"]) is int
                    and ledger["schema_version"] == 1
                    and quota_day.isoformat() == ledger["quota_day"]
                    and quota_day <= today
                    and all(
                        type(ledger[key]) is int and ledger[key] >= 0
                        for key in ("update_attempts", "used_units")
                    )
                    and all(
                        _number(ledger[key])
                        for key in ("next_update_at", "quota_pause_until")
                    )
                )
            except (KeyError, ValueError, TypeError) as exc:
                raise StateError("Invalid quota ledger") from exc
            if not valid:
                raise StateError("Invalid quota ledger")
            if quota_day < today:
                ledger.update(
                    quota_day=today.isoformat(),
                    update_attempts=0,
                    used_units=0,
                    quota_pause_until=0.0,
                )
                self._write(path, ledger)
        return ledger, now, reset_at

    def status(self) -> dict:
        with self._locked():
            ledger, _, reset_at = self._ledger()
            return {**ledger, "reset_at": reset_at}

    def reserve(self, cost: int, *, update=False) -> None:
        if type(cost) is not int or cost <= 0 or type(update) is not bool:
            raise StateError("Reservation requires a positive integer cost")
        with self._locked():
            ledger, now, reset_at = self._ledger()
            if ledger["quota_pause_until"] > now:
                raise DailyLimitError("quota_pause", reset_at)
            if update and ledger["update_attempts"] >= self.max_updates:
                raise DailyLimitError("update_attempts", reset_at)
            if ledger["used_units"] + cost > self.budget:
                raise DailyLimitError("quota_budget", reset_at)
            if update and ledger["next_update_at"] > now:
                raise SpacingError(ledger["next_update_at"])
            ledger["used_units"] += cost
            if update:
                ledger["update_attempts"] += 1
                ledger["next_update_at"] = now + self.interval
            self._write(self.root / "quota.json", ledger)

    def mark_quota_exhausted(self) -> None:
        with self._locked():
            ledger, _, reset_at = self._ledger()
            ledger["quota_pause_until"] = reset_at
            self._write(self.root / "quota.json", ledger)

    def _receipt(self, video_id, value):
        value = _mapping(value)
        if (
            type(value.get("schema_version")) is not int
            or value["schema_version"] != 1
            or value.get("video_id") != video_id
            or value.get("status")
            not in ("publishing", "published", "needs_reconciliation")
        ):
            raise StateError("Invalid receipt schema, video ID, or status")
        return value

    def read_receipt(self, video_id) -> dict | None:
        _video_id(video_id)
        with self._locked():
            value = self._read(self.receipts / f"{video_id}.json")
            return None if value is None else self._receipt(video_id, value)

    def write_receipt(self, video_id, value) -> None:
        _video_id(video_id)
        value = self._receipt(video_id, value)
        with self._locked():
            self._write(self.receipts / f"{video_id}.json", value)

    def _catalog(self, value):
        value = _mapping(value)
        if "videos" in value:
            if not isinstance(value["videos"], dict):
                raise StateError("Catalog videos must be a mapping")
            for video_id in value["videos"]:
                _video_id(video_id)
        return value

    def load_catalog(self) -> dict:
        with self._locked():
            value = self._read(self.root / "catalog.json")
            if value is None:
                return {}
            if (
                type(value.get("schema_version")) is not int
                or value["schema_version"] != 1
            ):
                raise StateError("Invalid catalog schema")
            if "data" not in value:
                raise StateError("Missing catalog data")
            return self._catalog(value["data"])

    def save_catalog(self, value: dict) -> None:
        value = self._catalog(value)
        with self._locked():
            self._write(
                self.root / "catalog.json", {"schema_version": 1, "data": value}
            )

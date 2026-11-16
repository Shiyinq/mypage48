"""Single-host ownership for independently deployed recorder controllers."""

import asyncio
import fcntl
import hashlib
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path


def recording_lock_name(live_id):
    return "recording-" + hashlib.sha256(live_id.encode()).hexdigest()


@contextmanager
def recording_lock(logs_dir, live_id):
    directory = Path(logs_dir) / "gdrive-claims"
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / recording_lock_name(live_id)).open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


@asynccontextmanager
async def async_recording_lock(logs_dir, live_id):
    directory = Path(logs_dir) / "gdrive-claims"
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / recording_lock_name(live_id)).open("a") as stream:
        while True:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                await asyncio.sleep(0.2)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


@contextmanager
def process_lock(logs_dir, role):
    path = Path(logs_dir)
    path.mkdir(parents=True, exist_ok=True)
    with (path / f".{role}.lock").open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(f"Another {role} controller is already running") from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)

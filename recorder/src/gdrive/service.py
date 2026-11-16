"""Independent, configuration-gated Drive service controller."""

import asyncio
import logging
import random

from ..process_lock import process_lock
from .backup_worker import BackupWorker
from .client import DriveClient
from .youtube_worker import YouTubeWorker

log = logging.getLogger("gdrive")


class GDriveService:
    def __init__(self, config):
        self.config = config

    async def run(self, stop_event):
        with process_lock(self.config.logs_dir, "gdrive"):
            if not self.config.backup_to_gdrive:
                log.info("GDrive processing disabled; service remains idle")
                await stop_event.wait()
                return
            if self.config.gdrive_max_concurrent_uploads < 1:
                raise ValueError("REC_GDRIVE_MAX_CONCURRENT_UPLOADS must be at least 1")
            if self.config.gdrive_to_youtube and self.config.max_concurrent_uploads < 1:
                raise ValueError("REC_MAX_CONCURRENT_UPLOADS must be at least 1")
            if not all(
                (
                    self.config.google_client_id,
                    self.config.google_client_secret,
                    self.config.gdrive_refresh_token,
                )
            ):
                raise ValueError(
                    "Drive backup enabled but Drive OAuth credentials are missing"
                )
            client = await asyncio.to_thread(DriveClient.from_config, self.config)
            await asyncio.to_thread(client.ensure_root)
            backup = BackupWorker(self.config, client)
            replay = YouTubeWorker(self.config, client)
            backup.stop_event = stop_event
            replay.stop_event = stop_event
            tasks = [
                asyncio.create_task(self._loop("backup", backup.scan_once, stop_event))
            ]
            if self.config.gdrive_to_youtube:
                tasks.append(
                    asyncio.create_task(
                        self._loop("YouTube", replay.scan_once, stop_event)
                    )
                )
            else:
                log.info("Backup-only mode; Drive-to-YouTube processing disabled")
            try:
                await asyncio.gather(*tasks)
            finally:
                stop_event.set()
                # Allow sync executor operations to finish rather than orphaning them.
                await asyncio.gather(*tasks, return_exceptions=True)
                await replay.close()

    async def _loop(self, label, scan, stop_event):
        failures = 0
        while not stop_event.is_set():
            try:
                await scan()
                failures = 0
            except Exception as exc:
                failures += 1
                log.error("GDrive %s scan failed (%s)", label, type(exc).__name__)
            delay = max(15, self.config.poll_interval)
            if failures:
                delay = min(900, delay * 2 ** min(failures, 5)) + random.uniform(0, 5)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=delay)
            except asyncio.TimeoutError:
                pass

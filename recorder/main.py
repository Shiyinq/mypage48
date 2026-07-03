import asyncio
import signal
import sys

from .src.config import RecorderConfig
from .src.logging_config import setup_logging
from .src.record.manager import RecordingManager
from .src.upload.watcher import Watcher


async def main():
    config = RecorderConfig()
    log_rec, log_upl = setup_logging(config)

    manager = RecordingManager(config, log_rec)
    watcher = Watcher(config, log_rec, log_upl)

    stop_event = asyncio.Event()

    def handle_signal():
        stop_event.set()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, handle_signal)
    loop.add_signal_handler(signal.SIGTERM, handle_signal)

    log_rec.info("Starting — poll interval %ss", config.poll_interval)
    log_rec.info("Output: %s", config.recordings_dir)

    recorder_task = asyncio.create_task(
        _run_recorder(manager, config, stop_event, log_rec)
    )
    watcher_task = asyncio.create_task(watcher.run(stop_event))

    await asyncio.gather(recorder_task, watcher_task)


async def _run_recorder(
    manager: RecordingManager,
    config: RecorderConfig,
    stop_event: asyncio.Event,
    log_rec,
):
    try:
        while not stop_event.is_set():
            try:
                lives, ok = await manager.detector.poll()

                if ok:
                    await manager.sync(lives)
                    await manager.check_health()
                    manager.log_progress()

            except Exception as e:
                log_rec.error("Loop error: %s", e)

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=config.poll_interval)
                break
            except asyncio.TimeoutError:
                pass
    finally:
        log_rec.info("Shutting down...")
        await manager.shutdown()
        log_rec.info("Goodbye.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)

import argparse
import asyncio
import signal
import sys

from .src.config import RecorderConfig
from .src.logging_config import setup_logging
from .src.record.manager import RecordingManager
from .src.upload.watcher import Watcher


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["both", "record", "upload"],
        default="both",
        help="Run mode: record, upload, or both (default)",
    )
    args = parser.parse_args()

    config = RecorderConfig()
    log_rec, log_upl = setup_logging(config)

    stop_event = asyncio.Event()

    def handle_signal():
        stop_event.set()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, handle_signal)
    loop.add_signal_handler(signal.SIGTERM, handle_signal)

    log_rec.info("Mode: %s — poll interval %ss", args.mode, config.poll_interval)
    log_rec.info("Output: %s", config.recordings_dir)

    tasks = []

    if args.mode in ("both", "record"):
        manager = RecordingManager(config, log_rec)
        tasks.append(asyncio.create_task(manager.run(stop_event)))

    if args.mode in ("both", "upload"):
        watcher = Watcher(config, log_rec, log_upl)
        tasks.append(asyncio.create_task(watcher.run(stop_event)))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)

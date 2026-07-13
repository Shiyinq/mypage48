import argparse
import asyncio
import signal
import sys

from .src.config import RecorderConfig
from .src.logging_config import setup_logging
from .src.record.manager import RecordingManager
from .src.theater.birthday_checker import BirthdayChecker
from .src.theater.idn_live_plus_checker import IdnLivePlusChecker
from .src.theater.mypage48_health_checker import HealthChecker
from .src.theater.news_checker import NewsChecker
from .src.theater.schedule_checker import ScheduleChecker
from .src.theater.watcher import TheaterWatcher
from .src.upload.watcher import Watcher


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["both", "record", "upload", "theater", "all"],
        default="both",
        help="Run mode: record, upload, theater, both (record+upload, default), or all",
    )
    parser.add_argument(
        "--status",
        nargs="?",
        const="all",
        help="Check the status of recordings. Use without value for 'all', or specify a folder name.",
    )
    parser.add_argument(
        "--remux",
        nargs="?",
        const="all",
        help="Force remux an interrupted recording. Use without value for 'all', or specify a folder name.",
    )
    parser.add_argument(
        "--delete",
        nargs="?",
        const="all",
        help="Delete recording folders. Use without value for 'all', or specify a folder name.",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Bypass confirmation prompts for destructive actions.",
    )
    return parser.parse_args()


def handle_cli(args):
    """Handle synchronous CLI commands (--status, --remux, --delete).
    Returns True if a CLI command was handled, False otherwise.
    """
    if not (args.status or args.remux or args.delete):
        return False

    config = RecorderConfig()
    log_rec, _, _ = setup_logging(config)
    manager = RecordingManager(config)

    if args.status:
        manager.check_status_cli(args.status)
    if args.remux:
        asyncio.run(manager.force_remux(args.remux))
    if args.delete:
        manager.delete_recordings_cli(args.delete, force=args.yes)

    return True


async def main(args):
    config = RecorderConfig()
    log_rec, log_upl, log_th = setup_logging(config)

    stop_event = asyncio.Event()

    def handle_signal():
        stop_event.set()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, handle_signal)
    loop.add_signal_handler(signal.SIGTERM, handle_signal)

    tasks = []

    if args.mode in ("all", "both", "record"):
        log_rec.info("Mode: %s — poll interval %ss", args.mode, config.poll_interval)
        log_rec.info("Output: %s", config.recordings_dir)
        manager = RecordingManager(config)
        tasks.append(asyncio.create_task(manager.run(stop_event)))

    if args.mode in ("all", "both", "upload"):
        log_upl.info("Mode: %s — poll interval %ss", args.mode, config.poll_interval)
        log_upl.info("Output: %s", config.recordings_dir)
        watcher = Watcher(config)
        tasks.append(asyncio.create_task(watcher.run(stop_event)))

    if args.mode in ("all", "theater"):
        log_th.info("Mode: %s — poll interval %ss", args.mode, config.poll_interval)
        log_th.info("Output: %s", config.recordings_dir)
        news_checker = NewsChecker(config)
        schedule_checker = ScheduleChecker(config)
        birthday_checker = BirthdayChecker(config)
        idn_live_plus_checker = IdnLivePlusChecker(config)
        health_checker = HealthChecker(config)
        theater_watcher = TheaterWatcher(config)

        tasks.append(asyncio.create_task(news_checker.run(stop_event)))
        tasks.append(asyncio.create_task(schedule_checker.run(stop_event)))
        tasks.append(asyncio.create_task(birthday_checker.run(stop_event)))
        tasks.append(asyncio.create_task(idn_live_plus_checker.run(stop_event)))
        tasks.append(asyncio.create_task(health_checker.run(stop_event)))
        tasks.append(asyncio.create_task(theater_watcher.run(stop_event)))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        args = parse_args()
        if not handle_cli(args):
            asyncio.run(main(args))
    except KeyboardInterrupt:
        sys.exit(0)

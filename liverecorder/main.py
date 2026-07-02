import asyncio
import signal
import sys

from .config import RecorderConfig
from .manager import RecordingManager


async def main():
    config = RecorderConfig()
    manager = RecordingManager(config)

    stop_event = asyncio.Event()

    def handle_signal():
        stop_event.set()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, handle_signal)
    loop.add_signal_handler(signal.SIGTERM, handle_signal)

    print(f"[liverecorder] Starting — poll interval {config.poll_interval}s")
    print(f"[liverecorder] Output: {config.recordings_dir}")

    try:
        while not stop_event.is_set():
            try:
                lives, ok = await manager.detector.poll()

                if ok:
                    await manager.sync(lives)
                    await manager.check_health()
                    manager.log_progress()

            except Exception as e:
                print(f"[liverecorder] Loop error: {e}")

            try:
                await asyncio.wait_for(
                    stop_event.wait(), timeout=config.poll_interval
                )
                break
            except asyncio.TimeoutError:
                pass
    finally:
        print("[liverecorder] Shutting down...")
        await manager.shutdown()
        print("[liverecorder] Goodbye.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)

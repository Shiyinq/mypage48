import os
import signal
import subprocess
import time


def start(hls_url: str, mkv_path: str) -> subprocess.Popen:
    os.makedirs(os.path.dirname(mkv_path), exist_ok=True)

    ffmpeg_log = os.path.splitext(mkv_path)[0] + ".ffmpeg.log"
    stderr_f = open(ffmpeg_log, "w")
    stderr_f.write(f"=== ffmpeg start at {time.time()} ===\n")
    stderr_f.write(f"URL: {hls_url}\n\n")
    stderr_f.flush()

    proc = subprocess.Popen(
        [
            "ffmpeg",
            "-live_start_index",
            "-3",
            "-i",
            hls_url,
            "-c",
            "copy",
            "-bsf:a",
            "aac_adtstoasc",
            "-f",
            "matroska",
            "-y",
            mkv_path,
        ],
        stdout=subprocess.DEVNULL,
        stderr=stderr_f,
    )
    return proc


def stop(proc: subprocess.Popen, timeout: int = 15):
    if proc.poll() is not None:
        return

    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def is_running(proc: subprocess.Popen) -> bool:
    return proc.poll() is None


def get_actual_duration(mkv_path: str) -> float:
    log_path = os.path.splitext(mkv_path)[0] + ".ffmpeg.log"

    if os.path.exists(log_path):
        try:
            with open(log_path) as f:
                import re

                for line in f:
                    m = re.search(r"time=(\d+):(\d+):(\d+)\.(\d+)", line)
                    if m:
                        h, mi, s, ms = map(int, m.groups())
                        return h * 3600 + mi * 60 + s + ms / 100
        except Exception:
            pass
    return 0.0

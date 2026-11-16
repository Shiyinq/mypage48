import asyncio
import logging
import os
import select
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from recorder import main


@pytest.fixture
def exit_mock(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(main.os, "_exit", mock)
    return mock


def assert_waiting(capsys):
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "waiting for in-flight work to finish safely" in captured.err
    assert "Press Ctrl+C again to force exit" in captured.err
    assert "Forcing exit" not in captured.err


def assert_forced(capsys):
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Forcing exit" in captured.err
    assert "active transfers/recordings may be interrupted" in captured.err
    assert "require recovery" in captured.err


def test_second_sigint_forces_exit(exit_mock, capsys):
    stop = asyncio.Event()
    handler = main._make_signal_handler(stop)

    handler(signal.SIGINT)
    assert stop.is_set()
    exit_mock.assert_not_called()
    assert_waiting(capsys)

    handler(signal.SIGINT)
    exit_mock.assert_called_once_with(130)
    assert_forced(capsys)


def test_repeated_sigterm_never_forces_exit(exit_mock, capsys):
    stop = asyncio.Event()
    handler = main._make_signal_handler(stop)

    handler(signal.SIGTERM)
    assert stop.is_set()
    assert_waiting(capsys)
    for _ in range(5):
        handler(signal.SIGTERM)
    assert stop.is_set()
    exit_mock.assert_not_called()
    assert capsys.readouterr() == ("", "")


def test_sigterm_does_not_count_as_sigint(exit_mock, capsys):
    stop = asyncio.Event()
    handler = main._make_signal_handler(stop)

    handler(signal.SIGTERM)
    assert_waiting(capsys)
    handler(signal.SIGINT)
    assert stop.is_set()
    exit_mock.assert_not_called()
    assert_waiting(capsys)

    handler(signal.SIGTERM)
    exit_mock.assert_not_called()
    assert capsys.readouterr() == ("", "")
    handler(signal.SIGINT)
    exit_mock.assert_called_once_with(130)
    assert_forced(capsys)


def test_shutdown_messages_bypass_file_logging(tmp_path, exit_mock, capsys):
    names = ("recorder", "uploader", "notify", "theater", "heartbeat", "gdrive")
    previous = {
        name: (list(logging.getLogger(name).handlers), logging.getLogger(name).level)
        for name in names
    }
    try:
        main.setup_logging(
            SimpleNamespace(logs_dir=str(tmp_path), log_level="INFO", log_mode="file")
        )
        logger = logging.getLogger("recorder")
        logger.info("file logging still works")
        for handler in logger.handlers:
            handler.flush()
        assert capsys.readouterr() == ("", "")

        stop = asyncio.Event()
        handler = main._make_signal_handler(stop)
        handler(signal.SIGINT)
        assert_waiting(capsys)
        handler(signal.SIGINT)
        assert_forced(capsys)
        exit_mock.assert_called_once_with(130)

        contents = "".join(path.read_text() for path in tmp_path.glob("*.log"))
        assert "file logging still works" in contents
        assert "Shutdown requested" not in contents
        assert "Forcing exit" not in contents
    finally:
        for name, (handlers, level) in previous.items():
            logger = logging.getLogger(name)
            for handler in list(logger.handlers):
                if handler not in handlers:
                    logger.removeHandler(handler)
                    handler.close()
            logger.handlers = handlers
            logger.setLevel(level)


@pytest.mark.skipif(os.name != "posix", reason="Requires POSIX asyncio signal handlers")
def test_second_sigint_exits_with_blocked_executor_thread():
    script = textwrap.dedent(
        """
        import asyncio
        import signal
        import threading
        from recorder.main import _make_signal_handler

        async def run():
            stop = asyncio.Event()
            started = threading.Event()
            blocked = threading.Event()

            def work():
                started.set()
                blocked.wait()

            loop = asyncio.get_running_loop()
            loop.add_signal_handler(
                signal.SIGINT, _make_signal_handler(stop), signal.SIGINT
            )
            worker = asyncio.create_task(asyncio.to_thread(work))
            while not started.is_set():
                await asyncio.sleep(0.01)
            print("READY", flush=True)
            await stop.wait()
            print("DRAINING", flush=True)
            await worker

        asyncio.run(run())
        """
    )
    process = subprocess.Popen(
        [sys.executable, "-u", "-c", script],
        cwd=Path(__file__).resolve().parents[2],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    def expect_line(expected, timeout=15):
        deadline = time.monotonic() + timeout
        received = bytearray()
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            readable, _, _ = select.select([process.stdout], [], [], max(0, remaining))
            assert readable, f"Timed out waiting for {expected!r}: {received!r}"
            chunk = os.read(process.stdout.fileno(), 1)
            assert chunk, f"Child closed stdout before {expected!r}: {received!r}"
            received.extend(chunk)
            if chunk == b"\n":
                assert received.decode().strip() == expected
                return
        pytest.fail(f"Timed out waiting for {expected!r}: {received!r}")

    try:
        expect_line("READY")
        process.send_signal(signal.SIGINT)
        expect_line("DRAINING", timeout=5)
        with pytest.raises(subprocess.TimeoutExpired):
            process.wait(timeout=0.25)

        process.send_signal(signal.SIGINT)
        assert process.wait(timeout=5) == 130
        _, stderr = process.communicate(timeout=2)
        assert b"waiting for in-flight work to finish safely" in stderr
        assert b"Forcing exit" in stderr
        assert b"require recovery" in stderr
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=5)

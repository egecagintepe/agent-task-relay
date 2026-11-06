"""Process lock mechanism and stale lock detection."""
from __future__ import annotations

import contextlib
import datetime as dt
import os
from pathlib import Path
import shutil
import socket
import sys

from agent_task_relay.errors import LockError


def is_pid_alive(pid: int) -> bool:
    """Check whether a process with the given PID is currently active."""
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.windll.kernel32
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        SYNCHRONIZE = 0x00100000
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, pid)
        if handle:
            exit_code = wintypes.DWORD()
            if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                kernel32.CloseHandle(handle)
                # STILL_ACTIVE is 259
                return exit_code.value == 259
            kernel32.CloseHandle(handle)
        return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False


@contextlib.contextmanager
def acquire_process_lock(config_dir: Path, lock_name: str = "run.lock"):
    """Acquire an atomic filesystem lock with stale lock reclamation."""
    lock_path = config_dir / lock_name
    owner_file = lock_path / "owner.txt"

    # Check for existing lock
    if lock_path.exists():
        is_stale = False
        owner_info = ""
        if owner_file.is_file():
            try:
                owner_info = owner_file.read_text(encoding="utf-8").strip()
                parts = owner_info.split()
                if parts:
                    pid = int(parts[0])
                    if not is_pid_alive(pid):
                        is_stale = True
            except Exception:
                is_stale = True
        else:
            is_stale = True

        if is_stale:
            try:
                shutil.rmtree(lock_path)
            except OSError as exc:
                raise LockError(f"Could not remove stale lock at {lock_path}: {exc}") from exc
        else:
            raise LockError(
                f"Watcher is already running or active lock held at {lock_path}.\n"
                f"Owner: {owner_info or 'Unknown'}"
            )

    try:
        lock_path.mkdir(parents=True)
    except FileExistsError as exc:
        raise LockError(f"Concurrent lock acquisition collision at {lock_path}") from exc

    pid = os.getpid()
    host = socket.gethostname()
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    owner_file.write_text(f"{pid} {host} {now_iso}\n", encoding="utf-8")

    try:
        yield
    finally:
        if lock_path.exists():
            shutil.rmtree(lock_path, ignore_errors=True)

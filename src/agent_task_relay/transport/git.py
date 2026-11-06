"""Git command wrapper and transport primitives."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import time

from agent_task_relay.errors import TransportError


def run_git(args: list[str], *, cwd: Path | None = None, timeout: int = 45) -> str:
    """Run a git command in the specified directory."""
    cmd = ["git"] + args
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise TransportError(f"Git command failed to execute: {' '.join(cmd)} ({exc})") from exc

    if proc.returncode != 0:
        err_msg = proc.stderr.strip() or proc.stdout.strip()
        raise TransportError(f"Git command failed (code {proc.returncode}): {' '.join(cmd)}\n{err_msg[:1200]}")

    return proc.stdout.strip()


class GitRepo:
    """Wrapper for Git operations on a repository directory."""

    def __init__(self, path: Path):
        self.path = path.resolve()

    def run_git(self, *args: str, timeout: int = 45) -> str:
        return run_git(["-C", str(self.path), *args], timeout=timeout)

    def is_valid_repo(self) -> bool:
        if not self.path.is_dir():
            return False
        try:
            res = run_git(["-C", str(self.path), "rev-parse", "--is-inside-work-tree"])
            return res == "true"
        except TransportError:
            return False

    def get_root(self) -> Path:
        root_str = run_git(["-C", str(self.path), "rev-parse", "--show-toplevel"])
        return Path(root_str).resolve()

    def has_remote(self) -> bool:
        try:
            remotes = run_git(["-C", str(self.path), "remote"])
            return bool(remotes.strip())
        except TransportError:
            return False

    def get_status_porcelain(self) -> str:
        return run_git(["-C", str(self.path), "status", "--porcelain"])

    def is_clean(self) -> bool:
        return not bool(self.get_status_porcelain().strip())

    def pull(self, ff_only: bool = True, timeout: int = 60) -> None:
        args = ["-C", str(self.path), "pull"]
        if ff_only:
            args.append("--ff-only")
        run_git(args, timeout=timeout)

    def add(self, relative_paths: list[str]) -> None:
        if not relative_paths:
            return
        args = ["-C", str(self.path), "add", "--"] + relative_paths
        run_git(args)

    def has_staged_changes(self) -> bool:
        out = run_git(["-C", str(self.path), "diff", "--cached", "--name-only"])
        return bool(out.strip())

    def commit(self, message: str) -> None:
        if not self.has_staged_changes():
            return
        run_git(["-C", str(self.path), "commit", "-m", message])

    def push(self, retries: int = 1, timeout: int = 90) -> None:
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                run_git(["-C", str(self.path), "push"], timeout=timeout)
                return
            except TransportError as exc:
                last_error = exc
                if attempt < retries:
                    time.sleep(1.0)
                    try:
                        self.pull(ff_only=True)
                    except TransportError:
                        pass
        raise TransportError(f"Failed to push changes to remote repository: {last_error}") from last_error

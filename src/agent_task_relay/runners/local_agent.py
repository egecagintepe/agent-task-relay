"""Local coding-agent harness runner adapter."""
from __future__ import annotations

import datetime as dt
from pathlib import Path
import shutil
import subprocess
import time

from agent_task_relay.errors import RunnerError
from agent_task_relay.protocol.models import RunnerResult, TaskPacket
from agent_task_relay.runners.base import BaseRunner
from agent_task_relay.transport.git import GitRepo


class LocalAgentHarnessRunner(BaseRunner):
    """Runner adapter for local agent harnesses (e.g. Ollama or local model harnesses).
    
    A raw local LLM is not an agent; it requires a harness with file access and tools.
    """

    name = "local"
    tier = "contract"
    description = (
        "Local coding-agent harness adapter (requires an agent wrapper capable of "
        "filesystem operations and tool execution, not merely a raw model endpoint)."
    )

    def is_available(self) -> tuple[bool, str]:
        # Check for local agent command wrapper, e.g. local-agent or ollama-agent
        for candidate in ("local-agent", "ollama-agent"):
            found = shutil.which(candidate)
            if found:
                return True, f"Local agent harness detected at {found}"
        return (
            False,
            "No local agent harness binary found. Note: a raw LLM (like 'ollama') is not a coding agent; "
            "it requires an agent harness capable of filesystem and tool operations. "
            "Use 'custom' runner or install a local agent CLI."
        )

    def run(
        self,
        task: TaskPacket,
        workspace: Path,
        timeout: int,
        log_dir: Path,
        custom_env: dict[str, str] | None = None,
    ) -> RunnerResult:
        available, reason = self.is_available()
        if not available:
            raise RunnerError(f"Local agent harness unavailable: {reason}")

        binary = "local-agent" if shutil.which("local-agent") else "ollama-agent"
        command = [binary, "--workspace", str(workspace.resolve()), "--task", str(task.file_path.resolve())]

        start_dt = dt.datetime.now(dt.timezone.utc)
        start_iso = start_dt.isoformat(timespec="seconds")
        start_mono = time.monotonic()

        stdout = ""
        stderr = ""
        exit_code = 0
        timed_out = False

        try:
            proc = subprocess.run(
                command,
                cwd=str(workspace),
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
                encoding="utf-8",
                errors="replace",
            )
            stdout = proc.stdout
            stderr = proc.stderr
            exit_code = proc.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = exc.stdout or ""
            stderr = f"TIMEOUT: Local agent timed out after {timeout} seconds.\n{exc.stderr or ''}"
            exit_code = -1
        except OSError as exc:
            stderr = f"OS Error starting {binary}: {exc}"
            exit_code = -2

        duration = round(time.monotonic() - start_mono, 2)
        end_iso = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

        log_path = self.write_log(log_dir, task.task_id, stdout, stderr)

        changed_files: list[str] = []
        repo = GitRepo(workspace)
        if repo.is_valid_repo():
            for line in repo.get_status_porcelain().splitlines():
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    changed_files.append(parts[1])

        blockers = self.check_approval_blocks(stdout + "\n" + stderr)

        if timed_out:
            status = "timeout"
            summary = f"Local agent harness timed out after {timeout} seconds."
        elif blockers:
            status = "needs-review"
            summary = "Local agent harness encountered approval barriers or restricted tools."
        elif exit_code == 0:
            status = "success"
            summary = stdout.strip()[:2000] if stdout.strip() else "Local agent harness executed successfully."
        else:
            status = "failure"
            summary = f"Local agent harness failed with code {exit_code}.\n{stderr.strip()[:1000]}"

        return RunnerResult(
            runner_name=self.name,
            task_id=task.task_id,
            status=status,
            exit_code=exit_code,
            summary=summary,
            changed_files=changed_files,
            test_results={},
            log_path=str(log_path),
            stdout=stdout,
            stderr=stderr,
            start_time=start_iso,
            end_time=end_iso,
            duration_seconds=duration,
            error_blockers=blockers,
        )

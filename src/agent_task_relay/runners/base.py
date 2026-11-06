"""Abstract base class and definitions for coding-agent runners."""
from __future__ import annotations

from abc import ABC, abstractmethod
import datetime as dt
from pathlib import Path
import re
from typing import Any

from agent_task_relay.protocol.models import RunnerResult, TaskPacket

# Common soft-denial or approval required patterns in agent output
APPROVAL_BLOCK_PATTERNS = [
    re.compile(r"permission denied", re.IGNORECASE),
    re.compile(r"approval required", re.IGNORECASE),
    re.compile(r"requires approval", re.IGNORECASE),
    re.compile(r"soft\.denied", re.IGNORECASE),
    re.compile(r"user denied", re.IGNORECASE),
    re.compile(r"unauthorized tool execution", re.IGNORECASE),
]


class BaseRunner(ABC):
    """Abstract base class for all coding agent runners."""

    name: str = "base"
    tier: str = "contract"  # "verified", "experimental", or "contract"
    description: str = ""

    @abstractmethod
    def is_available(self) -> tuple[bool, str]:
        """Check if runner prerequisites (executable, auth) are satisfied on this host."""
        pass

    @abstractmethod
    def run(
        self,
        task: TaskPacket,
        workspace: Path,
        timeout: int,
        log_dir: Path,
        custom_env: dict[str, str] | None = None,
    ) -> RunnerResult:
        """Execute the task within the designated workspace."""
        pass

    def check_approval_blocks(self, text: str) -> list[str]:
        """Detect any permission or tool execution denials in agent output."""
        blockers = []
        for pat in APPROVAL_BLOCK_PATTERNS:
            if pat.search(text):
                blockers.append(f"Detected runner permission restriction matching pattern: {pat.pattern}")
        return blockers

    def write_log(self, log_dir: Path, task_id: str, stdout: str, stderr: str) -> Path:
        """Write raw execution logs locally inside the project (never pushed to Git)."""
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{task_id}.log"
        content = (
            f"=== AGENT TASK RELAY LOCAL LOG ===\n"
            f"Task: {task_id}\n"
            f"Timestamp: {dt.datetime.now(dt.timezone.utc).isoformat()}\n"
            f"Runner: {self.name} ({self.tier})\n\n"
            f"--- STDOUT ---\n{stdout}\n\n"
            f"--- STDERR ---\n{stderr}\n"
        )
        log_file.write_text(content, encoding="utf-8", errors="replace")
        return log_file

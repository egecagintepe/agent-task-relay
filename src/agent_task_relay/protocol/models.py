"""Protocol data models and structures for Agent Task Relay."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any


class TaskState(str, Enum):
    """Lifecycle states for a task packet."""
    PENDING = "pending"
    APPROVED = "approved"
    CLAIMED = "claimed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs-review"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"
    EXPIRED = "expired"

    @classmethod
    def terminal_states(cls) -> set[TaskState]:
        return {
            cls.COMPLETED,
            cls.FAILED,
            cls.NEEDS_REVIEW,
            cls.REJECTED,
            cls.CANCELLED,
            cls.INTERRUPTED,
            cls.EXPIRED,
        }


@dataclass
class TaskPacket:
    """Represents an inbound task Markdown packet from the bridge inbox."""
    task_id: str
    file_path: Path
    raw_content: str
    sha256: str
    byte_size: int
    title: str = ""
    objective: str = ""
    context: str = ""
    scope: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)


@dataclass
class RunnerResult:
    """Structured result returned by any coding-agent runner."""
    runner_name: str
    task_id: str
    status: str  # "success", "failure", "needs-review", "timeout", "error"
    exit_code: int = 0
    summary: str = ""
    changed_files: list[str] = field(default_factory=list)
    test_results: dict[str, Any] = field(default_factory=dict)
    log_path: str | None = None
    stdout: str = ""
    stderr: str = ""
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0.0
    error_blockers: list[str] = field(default_factory=list)

    @property
    def is_success(self) -> bool:
        return self.status == "success" and self.exit_code == 0

    @property
    def needs_review(self) -> bool:
        return self.status == "needs-review"


@dataclass
class StateRecord:
    """Represents the persisted JSON state of a task in `state/<task_id>.json`."""
    task_id: str
    status: str
    sha256: str
    claimed_at: str
    host: str
    attempt: int = 1
    runner: str = "mock"
    started_at: str | None = None
    finished_at: str | None = None
    duration_seconds: float | None = None
    error: str | None = None
    rejection_reason: str | None = None
    changed_files: list[str] = field(default_factory=list)
    test_summary: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateRecord:
        known_fields = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)

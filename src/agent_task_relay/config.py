"""Configuration management and task approval tracking."""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any

from agent_task_relay.errors import ConfigurationError, SecurityError
from agent_task_relay.protocol.models import TaskPacket

CONFIG_DIR_NAME = ".agent-task-relay"
LEGACY_CONFIG_DIR_NAME = ".relaycrate"
CONFIG_FILE_NAME = "config.json"
APPROVED_FILE_NAME = "approved.json"


@dataclass
class CustomRunnerConfig:
    command: list[str] = field(default_factory=list)
    allowed_executables: list[str] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)


@dataclass
class RelayConfig:
    version: int = 1
    bridge: str = ""
    workspace: str = ""
    runner: str = "mock"
    poll_seconds: int = 60
    timeout_seconds: int = 3600
    approval_mode: str = "manual"  # "manual" | "auto"
    custom_runner: CustomRunnerConfig | None = None

    def validate(self) -> None:
        if not self.bridge:
            raise ConfigurationError("Bridge path must be specified.")
        if not self.workspace:
            raise ConfigurationError("Workspace path must be specified.")

        bridge_path = Path(self.bridge).expanduser().resolve()
        workspace_path = Path(self.workspace).expanduser().resolve()

        if not bridge_path.is_dir():
            raise ConfigurationError(f"Bridge path does not exist or is not a directory: {bridge_path}")
        if not workspace_path.is_dir():
            raise ConfigurationError(f"Workspace path does not exist or is not a directory: {workspace_path}")

        if bridge_path == workspace_path:
            raise SecurityError(
                f"Bridge and workspace must be separate directories. Both point to {bridge_path}"
            )

        if bridge_path in workspace_path.parents or workspace_path in bridge_path.parents:
            raise SecurityError(
                "Bridge directory and workspace directory cannot be nested within each other. "
                "Keep them strictly isolated."
            )

        if self.runner not in ("mock", "agy", "claude", "gemini", "codex", "opencode", "local", "custom"):
            raise ConfigurationError(f"Unsupported runner: {self.runner}")

        if self.approval_mode not in ("manual", "auto"):
            raise ConfigurationError(f"approval_mode must be 'manual' or 'auto', got {self.approval_mode}")

        if self.poll_seconds < 5:
            raise ConfigurationError("poll_seconds cannot be less than 5 seconds.")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.custom_runner is None:
            data.pop("custom_runner", None)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RelayConfig:
        custom_data = data.get("custom_runner")
        custom_obj = CustomRunnerConfig(**custom_data) if custom_data else None
        return cls(
            version=data.get("version", 1),
            bridge=data.get("bridge", ""),
            workspace=data.get("workspace", ""),
            runner=data.get("runner", "mock"),
            poll_seconds=int(data.get("poll_seconds", 60)),
            timeout_seconds=int(data.get("timeout_seconds", 3600)),
            approval_mode=data.get("approval_mode", "manual"),
            custom_runner=custom_obj,
        )


def find_config_dir(start_path: Path | None = None) -> Path | None:
    """Search upwards for the configuration directory."""
    path = (start_path or Path.cwd()).expanduser().resolve()
    for parent in (path, *path.parents):
        cand = parent / CONFIG_DIR_NAME
        if cand.is_dir() and (cand / CONFIG_FILE_NAME).is_file():
            return cand
        cand_legacy = parent / LEGACY_CONFIG_DIR_NAME
        if cand_legacy.is_dir() and (cand_legacy / CONFIG_FILE_NAME).is_file():
            return cand_legacy
    return None


def resolve_config_file(explicit_path: str | Path | None = None) -> Path:
    """Resolve the path to the configuration file."""
    if explicit_path:
        p = Path(explicit_path).expanduser().resolve()
        if p.is_dir():
            cand = p / CONFIG_FILE_NAME
            if cand.is_file():
                return cand
        elif p.is_file():
            return p
        raise ConfigurationError(f"Specified configuration file not found: {p}")

    cdir = find_config_dir()
    if cdir:
        return cdir / CONFIG_FILE_NAME

    raise ConfigurationError(
        f"Configuration not found. Searched for {CONFIG_DIR_NAME}/{CONFIG_FILE_NAME} in current and parent directories. "
        "Run `agent-task-relay init` first or specify --config PATH."
    )


def load_config(explicit_path: str | Path | None = None) -> tuple[Path, RelayConfig]:
    """Load and validate the RelayConfig."""
    cfg_file = resolve_config_file(explicit_path)
    try:
        data = json.loads(cfg_file.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ConfigurationError(f"Failed to read JSON config at {cfg_file}: {exc}") from exc

    cfg = RelayConfig.from_dict(data)
    cfg.validate()
    return cfg_file, cfg


def save_config(cfg_file: Path, cfg: RelayConfig) -> None:
    """Save configuration to disk atomically."""
    cfg.validate()
    cfg_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file = cfg_file.with_name(cfg_file.name + ".tmp")
    temp_file.write_text(json.dumps(cfg.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp_file.replace(cfg_file)


def get_approved_file(config_dir: Path) -> Path:
    return config_dir / APPROVED_FILE_NAME


def load_approved_tasks(config_dir: Path) -> dict[str, dict[str, str]]:
    """Load approved tasks mapping: task_id -> {sha256, approved_at}."""
    app_file = get_approved_file(config_dir)
    if not app_file.is_file():
        return {}
    try:
        data = json.loads(app_file.read_text(encoding="utf-8"))
    except Exception:
        return {}

    # Migration / compatibility with legacy format {"task_ids": ["TASK-01"]}
    if "tasks" in data and isinstance(data["tasks"], dict):
        return data["tasks"]
    elif "task_ids" in data and isinstance(data["task_ids"], list):
        return {tid: {"sha256": "", "approved_at": ""} for tid in data["task_ids"]}
    return {}


def save_approved_tasks(config_dir: Path, tasks: dict[str, dict[str, str]]) -> None:
    """Save approved tasks mapping to disk atomically."""
    app_file = get_approved_file(config_dir)
    app_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file = app_file.with_name(app_file.name + ".tmp")
    data = {"version": 1, "tasks": tasks}
    temp_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp_file.replace(app_file)


def record_task_approval(config_dir: Path, task_id: str, sha256: str) -> None:
    """Record an approval for a specific task and exact content SHA-256 hash."""
    tasks = load_approved_tasks(config_dir)
    tasks[task_id] = {
        "sha256": sha256,
        "approved_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    save_approved_tasks(config_dir, tasks)


def verify_task_approval(config_dir: Path, packet: TaskPacket, approval_mode: str) -> tuple[bool, str]:
    """Verify whether a task is approved and whether its content has been tampered with.
    
    Returns (is_approved, reason).
    """
    if approval_mode == "auto":
        return True, "Auto-approval enabled"

    tasks = load_approved_tasks(config_dir)
    if packet.task_id not in tasks:
        return False, f"Task {packet.task_id} has not been approved. Run `approve {packet.task_id} --yes`."

    record = tasks[packet.task_id]
    if not isinstance(record, dict):
        return False, f"Invalid approval record format for {packet.task_id}. Re-run `approve {packet.task_id} --yes`."

    recorded_sha = record.get("sha256", "")

    # Strict check: Approval MUST have a stored, non-empty cryptographic hash.
    # Legacy approval records with empty SHA-256 are rejected.
    if not recorded_sha:
        return False, (
            f"SECURITY ALERT: Task {packet.task_id} was approved under a legacy format without a content SHA-256 hash. "
            f"To prevent execution of unverified content, re-review the task and run `approve {packet.task_id} --yes`."
        )

    # The recorded hash MUST match the current packet hash exactly
    if recorded_sha != packet.sha256:
        return False, (
            f"SECURITY ALERT: Task {packet.task_id} content was modified after approval!\n"
            f"Approved SHA-256: {recorded_sha}\n"
            f"Current SHA-256:  {packet.sha256}\n"
            f"Re-review task contents and re-run `approve {packet.task_id} --yes`."
        )

    return True, "Approved with matching SHA-256"

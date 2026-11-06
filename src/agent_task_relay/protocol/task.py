"""Task packet parsing, validation, and ID verification."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re

from agent_task_relay.errors import TaskValidationError, SecurityError
from agent_task_relay.protocol.models import TaskPacket

TASK_ID_PATTERN = re.compile(r"^TASK-[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
TASK_FILE_PATTERN = re.compile(r"^TASK-[A-Za-z0-9][A-Za-z0-9._-]{0,79}\.md$")
MAX_TASK_BYTES = 200_000


def validate_task_id(raw: str) -> str:
    """Validate a task identifier string.
    
    Must match `TASK-<alphanumeric/dot/dash/underscore>`, max 85 chars total.
    Rejects path separators, directory traversal, or malicious input.
    """
    if not raw or not isinstance(raw, str):
        raise TaskValidationError("Task ID cannot be empty.")
    if "/" in raw or "\\" in raw or ".." in raw or "\0" in raw:
        raise SecurityError(f"Task ID contains forbidden characters or path separators: {raw!r}")
    if not TASK_ID_PATTERN.fullmatch(raw):
        raise TaskValidationError(
            f"Invalid task ID {raw!r}. Must match 'TASK-<chars>' using letters, numbers, '.', '_', '-', max 85 chars."
        )
    return raw


def validate_task_file_name(name: str) -> str:
    """Validate a task file name, returning the task ID."""
    if not TASK_FILE_PATTERN.fullmatch(name):
        raise TaskValidationError(f"Invalid task filename: {name!r}. Expected TASK-<ID>.md")
    return name[:-3]


def parse_task_file(path: Path, max_bytes: int = MAX_TASK_BYTES) -> TaskPacket:
    """Read and validate a task file from disk into a TaskPacket."""
    if path.is_symlink():
        raise SecurityError(f"Symlinks are forbidden for task files: {path}")
    if not path.is_file():
        raise TaskValidationError(f"Task file not found or not a regular file: {path}")

    task_id = validate_task_file_name(path.name)

    size = path.stat().st_size
    if size == 0:
        raise TaskValidationError(f"Task file {path.name} is empty.")
    if size > max_bytes:
        raise TaskValidationError(
            f"Task file {path.name} exceeds maximum allowed size ({size} > {max_bytes} bytes)."
        )

    try:
        content_bytes = path.read_bytes()
        raw_text = content_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TaskValidationError(f"Task file {path.name} is not valid UTF-8: {exc}") from exc

    sha256 = hashlib.sha256(content_bytes).hexdigest()

    # Extract sections
    title = ""
    objective = ""
    context = ""
    scope = ""
    acceptance_criteria: list[str] = []

    lines = raw_text.splitlines()
    current_section = ""
    section_buffers: dict[str, list[str]] = {
        "objective": [],
        "context": [],
        "scope": [],
        "acceptance": [],
    }

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# ") and not title:
            title = stripped[2:].strip()
            continue
        if stripped.lower().startswith("## objective"):
            current_section = "objective"
            continue
        elif stripped.lower().startswith("## context"):
            current_section = "context"
            continue
        elif stripped.lower().startswith("## scope"):
            current_section = "scope"
            continue
        elif stripped.lower().startswith("## acceptance criteria") or stripped.lower().startswith("## acceptance"):
            current_section = "acceptance"
            continue
        elif stripped.startswith("## "):
            current_section = ""
            continue

        if current_section in section_buffers:
            section_buffers[current_section].append(line)

    objective = "\n".join(section_buffers["objective"]).strip()
    context = "\n".join(section_buffers["context"]).strip()
    scope = "\n".join(section_buffers["scope"]).strip()

    for item in section_buffers["acceptance"]:
        item_str = item.strip()
        if item_str.startswith("- [ ]") or item_str.startswith("- [x]") or item_str.startswith("- *") or item_str.startswith("-"):
            crit = item_str.lstrip("- [* ]").strip()
            if crit:
                acceptance_criteria.append(crit)

    return TaskPacket(
        task_id=task_id,
        file_path=path,
        raw_content=raw_text,
        sha256=sha256,
        byte_size=size,
        title=title or task_id,
        objective=objective,
        context=context,
        scope=scope,
        acceptance_criteria=acceptance_criteria,
    )

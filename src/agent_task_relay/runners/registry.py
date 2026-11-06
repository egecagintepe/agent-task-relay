"""Runner registry and factory."""
from __future__ import annotations

from typing import Any

from agent_task_relay.config import RelayConfig
from agent_task_relay.errors import ConfigurationError
from agent_task_relay.runners.antigravity import AntigravityRunner
from agent_task_relay.runners.base import BaseRunner
from agent_task_relay.runners.claude_code import ClaudeCodeRunner
from agent_task_relay.runners.codex_cli import CodexCliRunner
from agent_task_relay.runners.custom import CustomCommandRunner
from agent_task_relay.runners.gemini_cli import GeminiCliRunner
from agent_task_relay.runners.local_agent import LocalAgentHarnessRunner
from agent_task_relay.runners.mock import MockRunner
from agent_task_relay.runners.opencode import OpenCodeRunner

RUNNER_CLASSES: dict[str, type[BaseRunner]] = {
    "mock": MockRunner,
    "agy": AntigravityRunner,
    "claude": ClaudeCodeRunner,
    "gemini": GeminiCliRunner,
    "codex": CodexCliRunner,
    "opencode": OpenCodeRunner,
    "local": LocalAgentHarnessRunner,
}


def get_runner(name: str, config: RelayConfig | None = None) -> BaseRunner:
    """Retrieve an instantiated runner by name."""
    if name == "custom":
        custom_cfg = config.custom_runner if config else None
        cmd = custom_cfg.command if custom_cfg else []
        allowed = custom_cfg.allowed_executables if custom_cfg else None
        return CustomCommandRunner(command_template=cmd, allowed_executables=allowed)

    cls = RUNNER_CLASSES.get(name)
    if not cls:
        raise ConfigurationError(
            f"Unknown runner: {name!r}. Supported runners: {sorted(list(RUNNER_CLASSES.keys()) + ['custom'])}"
        )
    return cls()


def list_runners(config: RelayConfig | None = None) -> list[dict[str, Any]]:
    """List all available runners, their support tier, and local availability status."""
    results = []
    all_names = list(RUNNER_CLASSES.keys()) + ["custom"]
    for name in all_names:
        runner = get_runner(name, config)
        avail, reason = runner.is_available()
        results.append({
            "name": runner.name,
            "tier": runner.tier,
            "description": runner.description,
            "available": avail,
            "status_message": reason,
        })
    return results

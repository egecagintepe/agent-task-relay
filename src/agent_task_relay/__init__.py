"""Agent Task Relay: Bridge any AI chat to any coding agent through Git.

A vendor-agnostic, zero-external-dependency local task relay and Agent Skill
for coordinating software engineering tasks between chat assistants and coding agents.
"""

__version__ = "0.2.0"
__author__ = "Ege Çağın Tepe"
__license__ = "PolyForm Internal Use License 1.0.0"

from agent_task_relay.protocol.models import TaskPacket, TaskState, StateRecord, RunnerResult
from agent_task_relay.config import RelayConfig, load_config

__all__ = [
    "__version__",
    "TaskPacket",
    "TaskState",
    "StateRecord",
    "RunnerResult",
    "RelayConfig",
    "load_config",
]

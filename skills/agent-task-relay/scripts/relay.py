#!/usr/bin/env python3
"""Agent Task Relay Skill CLI wrapper.

Executes the authoritative `agent_task_relay` execution engine.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys

# Ensure agent_task_relay is importable if running directly from repo or skill folder
current_file = Path(__file__).resolve()
repo_root = current_file.parents[3]
src_dir = repo_root / "src"
if src_dir.is_dir() and str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

try:
    from agent_task_relay.cli import main
except ImportError:
    # If installed as a standalone skill folder inside a project
    project_root = current_file.parents[3]
    print(
        f"Notice: `agent_task_relay` package not installed in environment.\n"
        f"Install with: pip install agent-task-relay\n"
        f"Or run from repository source.\n",
        file=sys.stderr,
    )
    sys.exit(1)

if __name__ == "__main__":
    main()

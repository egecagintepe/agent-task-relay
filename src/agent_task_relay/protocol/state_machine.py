"""Task state machine and transition validation."""
from __future__ import annotations

from agent_task_relay.errors import StateTransitionError
from agent_task_relay.protocol.models import TaskState

VALID_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.PENDING: {
        TaskState.APPROVED,
        TaskState.CLAIMED,  # allowed in auto-approval mode
        TaskState.REJECTED,
        TaskState.CANCELLED,
        TaskState.EXPIRED,
    },
    TaskState.APPROVED: {
        TaskState.CLAIMED,
        TaskState.REJECTED,
        TaskState.CANCELLED,
    },
    TaskState.CLAIMED: {
        TaskState.RUNNING,
        TaskState.INTERRUPTED,
        TaskState.FAILED,
        # Direct terminal transitions for simple/mock runners:
        TaskState.COMPLETED,
        TaskState.NEEDS_REVIEW,
    },
    TaskState.RUNNING: {
        TaskState.COMPLETED,
        TaskState.FAILED,
        TaskState.NEEDS_REVIEW,
        TaskState.INTERRUPTED,
    },
    TaskState.COMPLETED: set(),
    TaskState.FAILED: set(),
    TaskState.NEEDS_REVIEW: set(),
    TaskState.REJECTED: set(),
    TaskState.CANCELLED: set(),
    TaskState.INTERRUPTED: set(),
    TaskState.EXPIRED: set(),
}


class TaskStateMachine:
    """Validates and applies task state transitions."""

    @staticmethod
    def can_transition(current: str | TaskState, target: str | TaskState) -> bool:
        curr_state = TaskState(current) if isinstance(current, str) else current
        tgt_state = TaskState(target) if isinstance(target, str) else target
        return tgt_state in VALID_TRANSITIONS.get(curr_state, set())

    @classmethod
    def validate_transition(
        cls, task_id: str, current: str | TaskState, target: str | TaskState
    ) -> None:
        curr_state = TaskState(current) if isinstance(current, str) else current
        tgt_state = TaskState(target) if isinstance(target, str) else target
        if not cls.can_transition(curr_state, tgt_state):
            raise StateTransitionError(
                f"Invalid state transition for {task_id}: {curr_state.value} -> {tgt_state.value}. "
                f"Allowed target states from {curr_state.value}: "
                f"{[s.value for s in VALID_TRANSITIONS.get(curr_state, set())]}"
            )

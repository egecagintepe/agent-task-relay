"""Tests for task lifecycle state transitions and invariants."""
import unittest

from agent_task_relay.errors import StateTransitionError
from agent_task_relay.protocol.models import TaskState
from agent_task_relay.protocol.state_machine import TaskStateMachine


class TestStateMachine(unittest.TestCase):
    def test_valid_forward_transitions(self):
        # PENDING -> APPROVED -> CLAIMED -> RUNNING -> COMPLETED
        TaskStateMachine.validate_transition("TASK-1", TaskState.PENDING, TaskState.APPROVED)
        TaskStateMachine.validate_transition("TASK-1", TaskState.APPROVED, TaskState.CLAIMED)
        TaskStateMachine.validate_transition("TASK-1", TaskState.CLAIMED, TaskState.RUNNING)
        TaskStateMachine.validate_transition("TASK-1", TaskState.RUNNING, TaskState.COMPLETED)

    def test_direct_claim_in_auto_mode(self):
        TaskStateMachine.validate_transition("TASK-1", TaskState.PENDING, TaskState.CLAIMED)

    def test_rejection_and_cancellation(self):
        TaskStateMachine.validate_transition("TASK-1", TaskState.PENDING, TaskState.REJECTED)
        TaskStateMachine.validate_transition("TASK-1", TaskState.PENDING, TaskState.CANCELLED)
        TaskStateMachine.validate_transition("TASK-1", TaskState.APPROVED, TaskState.REJECTED)

    def test_runner_outcomes(self):
        TaskStateMachine.validate_transition("TASK-1", TaskState.RUNNING, TaskState.FAILED)
        TaskStateMachine.validate_transition("TASK-1", TaskState.RUNNING, TaskState.NEEDS_REVIEW)
        TaskStateMachine.validate_transition("TASK-1", TaskState.CLAIMED, TaskState.COMPLETED)
        TaskStateMachine.validate_transition("TASK-1", TaskState.CLAIMED, TaskState.NEEDS_REVIEW)

    def test_terminal_states_cannot_transition(self):
        terminal_states = TaskState.terminal_states()
        for term in terminal_states:
            for other in TaskState:
                with self.assertRaises(StateTransitionError):
                    TaskStateMachine.validate_transition("TASK-1", term, other)

    def test_invalid_backward_transitions(self):
        with self.assertRaises(StateTransitionError):
            TaskStateMachine.validate_transition("TASK-1", TaskState.RUNNING, TaskState.PENDING)
        with self.assertRaises(StateTransitionError):
            TaskStateMachine.validate_transition("TASK-1", TaskState.CLAIMED, TaskState.APPROVED)


if __name__ == "__main__":
    unittest.main()

"""Tests for task session state machine (FSM) invariants and transitions."""

import unittest

from agent_gauntlet.features.supervisor.core.fsm import SessionFsm, SessionFsmError
from agent_gauntlet.features.supervisor.core.models import SessionState


class TestSessionFsm(unittest.TestCase):
    """Verifies that the session FSM transitions deterministically and fails closed."""

    def setUp(self) -> None:
        self.fsm = SessionFsm()

    def test_initial_state_is_discovered(self) -> None:
        """New task session begins in DISCOVERED state."""
        session = self.fsm.create_session(
            session_id="sess-001",
            workspace_id="ws-abc",
            task_id="035-supervisor",
            task_digest="sha256:12345678",
        )
        self.assertEqual(session.state, SessionState.DISCOVERED)

    def test_transition_discovered_to_active(self) -> None:
        """Session transitions from DISCOVERED to ACTIVE upon session start/resume."""
        session = self.fsm.create_session(
            session_id="sess-001",
            workspace_id="ws-abc",
            task_id="035-supervisor",
            task_digest="sha256:12345678",
        )
        active_session = self.fsm.activate_session(session)
        self.assertEqual(active_session.state, SessionState.ACTIVE)

    def test_transition_active_to_verifying(self) -> None:
        """Session transitions from ACTIVE to VERIFYING when verification starts."""
        session = self.fsm.create_session(
            session_id="sess-001",
            workspace_id="ws-abc",
            task_id="035-supervisor",
            task_digest="sha256:12345678",
        )
        session = self.fsm.activate_session(session)
        verifying_session = self.fsm.start_verification(session, snapshot_digest="sha256:snap123")
        self.assertEqual(verifying_session.state, SessionState.VERIFYING)
        self.assertEqual(verifying_session.snapshot_digest, "sha256:snap123")

    def test_transition_verifying_to_passed_or_failed(self) -> None:
        """Session completes verification transitioning to PASSED or FAILED."""
        session = self.fsm.create_session(
            session_id="sess-001",
            workspace_id="ws-abc",
            task_id="035-supervisor",
            task_digest="sha256:12345678",
        )
        session = self.fsm.activate_session(session)
        session = self.fsm.start_verification(session, snapshot_digest="sha256:snap123")

        passed_session = self.fsm.finish_verification(session, passed=True)
        self.assertEqual(passed_session.state, SessionState.PASSED)

    def test_illegal_transition_raises_fail_closed_error(self) -> None:
        """Attempting an illegal transition (e.g. DISCOVERED directly to PASSED) raises error."""
        session = self.fsm.create_session(
            session_id="sess-001",
            workspace_id="ws-abc",
            task_id="035-supervisor",
            task_digest="sha256:12345678",
        )
        with self.assertRaises(SessionFsmError):
            self.fsm.finish_verification(session, passed=True)

    def test_invalidation_upon_continuity_or_digest_break(self) -> None:
        """Session is marked INVALIDATED when state drift or log break occurs."""
        session = self.fsm.create_session(
            session_id="sess-001",
            workspace_id="ws-abc",
            task_id="035-supervisor",
            task_digest="sha256:12345678",
        )
        session = self.fsm.activate_session(session)
        invalid_session = self.fsm.invalidate_session(
            session, reason="Task contract digest drifted during run"
        )
        self.assertEqual(invalid_session.state, SessionState.INVALIDATED)
        self.assertIn("Task contract digest drifted", invalid_session.invalidation_reason)


if __name__ == "__main__":
    unittest.main()

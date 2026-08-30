"""Deterministic Task Session Finite State Machine (FSM) with fail-closed semantics."""

from __future__ import annotations

from datetime import datetime, timezone

from agent_gauntlet.features.supervisor.core.models import SessionState, TaskSessionRecord


class SessionFsmError(Exception):
    """Raised when an illegal or corrupt session transition is attempted."""


class SessionFsm:
    """Orchestrates deterministic, invariant-preserving task session state transitions."""

    @staticmethod
    def _now_utc() -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_session(
        self,
        session_id: str,
        workspace_id: str,
        task_id: str,
        task_digest: str,
    ) -> TaskSessionRecord:
        """Initializes a new session in DISCOVERED state."""
        now = self._now_utc()
        return TaskSessionRecord(
            session_id=session_id,
            workspace_id=workspace_id,
            task_id=task_id,
            task_digest=task_digest,
            state=SessionState.DISCOVERED,
            created_at_utc=now,
            updated_at_utc=now,
        )

    def activate_session(self, session: TaskSessionRecord) -> TaskSessionRecord:
        """Transitions a session from DISCOVERED or ACTIVE to ACTIVE."""
        if session.state not in (SessionState.DISCOVERED, SessionState.ACTIVE):
            raise SessionFsmError(
                f"Cannot activate session in state '{session.state.value}' (expected DISCOVERED or ACTIVE)"
            )
        now = self._now_utc()
        return TaskSessionRecord(
            session_id=session.session_id,
            workspace_id=session.workspace_id,
            task_id=session.task_id,
            task_digest=session.task_digest,
            state=SessionState.ACTIVE,
            snapshot_digest=session.snapshot_digest,
            invalidation_reason=session.invalidation_reason,
            created_at_utc=session.created_at_utc,
            updated_at_utc=now,
            event_count=session.event_count,
            event_log_root=session.event_log_root,
        )

    def start_verification(
        self,
        session: TaskSessionRecord,
        snapshot_digest: str,
    ) -> TaskSessionRecord:
        """Transitions a session from ACTIVE to VERIFYING."""
        if session.state != SessionState.ACTIVE:
            raise SessionFsmError(
                f"Cannot start verification from state '{session.state.value}' (expected ACTIVE)"
            )
        now = self._now_utc()
        return TaskSessionRecord(
            session_id=session.session_id,
            workspace_id=session.workspace_id,
            task_id=session.task_id,
            task_digest=session.task_digest,
            state=SessionState.VERIFYING,
            snapshot_digest=snapshot_digest,
            invalidation_reason=session.invalidation_reason,
            created_at_utc=session.created_at_utc,
            updated_at_utc=now,
            event_count=session.event_count,
            event_log_root=session.event_log_root,
        )

    def finish_verification(
        self,
        session: TaskSessionRecord,
        passed: bool,
    ) -> TaskSessionRecord:
        """Transitions a session from VERIFYING to PASSED or FAILED."""
        if session.state != SessionState.VERIFYING:
            raise SessionFsmError(
                f"Cannot finish verification from state '{session.state.value}' (expected VERIFYING)"
            )
        now = self._now_utc()
        next_state = SessionState.PASSED if passed else SessionState.FAILED
        return TaskSessionRecord(
            session_id=session.session_id,
            workspace_id=session.workspace_id,
            task_id=session.task_id,
            task_digest=session.task_digest,
            state=next_state,
            snapshot_digest=session.snapshot_digest,
            invalidation_reason=session.invalidation_reason,
            created_at_utc=session.created_at_utc,
            updated_at_utc=now,
            event_count=session.event_count,
            event_log_root=session.event_log_root,
        )

    def invalidate_session(
        self,
        session: TaskSessionRecord,
        reason: str,
    ) -> TaskSessionRecord:
        """Transitions any non-closed session to INVALIDATED."""
        if session.state == SessionState.CLOSED:
            raise SessionFsmError("Cannot invalidate an already closed session")
        now = self._now_utc()
        return TaskSessionRecord(
            session_id=session.session_id,
            workspace_id=session.workspace_id,
            task_id=session.task_id,
            task_digest=session.task_digest,
            state=SessionState.INVALIDATED,
            snapshot_digest=session.snapshot_digest,
            invalidation_reason=reason,
            created_at_utc=session.created_at_utc,
            updated_at_utc=now,
            event_count=session.event_count,
            event_log_root=session.event_log_root,
        )

    def close_session(self, session: TaskSessionRecord) -> TaskSessionRecord:
        """Finalizes a session into CLOSED state."""
        if session.state not in (
            SessionState.PASSED,
            SessionState.FAILED,
            SessionState.INVALIDATED,
        ):
            raise SessionFsmError(
                f"Cannot close session in state '{session.state.value}' (must be PASSED, FAILED, or INVALIDATED)"
            )
        now = self._now_utc()
        return TaskSessionRecord(
            session_id=session.session_id,
            workspace_id=session.workspace_id,
            task_id=session.task_id,
            task_digest=session.task_digest,
            state=SessionState.CLOSED,
            snapshot_digest=session.snapshot_digest,
            invalidation_reason=session.invalidation_reason,
            created_at_utc=session.created_at_utc,
            updated_at_utc=now,
            event_count=session.event_count,
            event_log_root=session.event_log_root,
        )

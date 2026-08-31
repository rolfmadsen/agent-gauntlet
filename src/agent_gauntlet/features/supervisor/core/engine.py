"""Supervisor Core Engine orchestrating workspace registration, session FSM, and RPC dispatching."""

from __future__ import annotations

import hashlib
from pathlib import Path

from agent_gauntlet.features.supervisor.core.event_log import SessionEventLog
from agent_gauntlet.features.supervisor.core.fsm import SessionFsm
from agent_gauntlet.features.supervisor.core.models import (
    CapabilityRequest,
    EnforcementContext,
    RpcMethod,
    RpcRequest,
    RpcResponse,
    SessionState,
    TaskSessionRecord,
)
from agent_gauntlet.features.supervisor.platform.linux.keys import LinuxKeyProvider, TaskCertificate
from agent_gauntlet.features.supervisor.wasm.verifier import WasmPolicyVerifier


class SupervisorEngine:
    """Central daemon engine managing workspaces, active sessions, WASM verification, and RPCs."""

    VERSION = "0.7.0"

    def __init__(
        self,
        key_provider: LinuxKeyProvider | None = None,
        policy_verifier: WasmPolicyVerifier | None = None,
    ) -> None:
        self.key_provider = key_provider or LinuxKeyProvider()
        self.policy_verifier = policy_verifier or WasmPolicyVerifier()
        self.fsm = SessionFsm()

        self._workspaces: dict[str, Path] = {}
        self._sessions: dict[str, TaskSessionRecord] = {}
        self._certificates: dict[str, TaskCertificate] = {}
        self._event_logs: dict[str, SessionEventLog] = {}

    def register_workspace(self, workspace_path: str, workspace_id: str) -> None:
        """Registers a workspace root path."""
        path = Path(workspace_path).resolve()
        self._workspaces[workspace_id] = path

    def begin_or_resume_session(
        self,
        workspace_id: str,
        task_id: str,
    ) -> tuple[TaskSessionRecord, TaskCertificate]:
        """Activates or resumes a task session and issues a task certificate."""
        session_id = f"sess_{workspace_id}_{task_id}"
        task_digest = f"sha256:{hashlib.sha256(task_id.encode('utf-8')).hexdigest()}"
        wasm_digest = f"sha256:{hashlib.sha256(self.policy_verifier.get_policy_version().encode('utf-8')).hexdigest()}"

        if session_id not in self._sessions:
            session = self.fsm.create_session(
                session_id=session_id,
                workspace_id=workspace_id,
                task_id=task_id,
                task_digest=task_digest,
            )
            session = self.fsm.activate_session(session)
            self._sessions[session_id] = session

            cert = self.key_provider.issue_task_certificate(
                workspace_id=workspace_id,
                task_id=task_id,
                task_digest=task_digest,
                wasm_digest=wasm_digest,
            )
            self._certificates[session_id] = cert

            log = SessionEventLog(session_id=session_id)
            log.append("SESSION_START", {"workspace_id": workspace_id, "task_id": task_id})
            self._event_logs[session_id] = log
        else:
            session = self._sessions[session_id]
            if session.state == SessionState.DISCOVERED:
                session = self.fsm.activate_session(session)
                self._sessions[session_id] = session
            cert = self._certificates[session_id]

        return session, cert

    def handle_rpc(self, request: RpcRequest) -> RpcResponse:
        """Dispatches incoming RPC requests to internal handler methods."""
        try:
            if request.method == RpcMethod.GET_STATUS:
                return RpcResponse(
                    id=request.id,
                    result={
                        "status": "HEALTHY",
                        "version": self.VERSION,
                        "installation_public_key": self.key_provider.get_installation_public_key(),
                        "active_workspaces": len(self._workspaces),
                        "active_sessions": len(self._sessions),
                    },
                )

            if request.method == RpcMethod.REGISTER_WORKSPACE:
                ws_path = str(request.params.get("workspace_path", "."))
                ws_id = str(request.params.get("workspace_id", "default"))
                self.register_workspace(ws_path, ws_id)
                return RpcResponse(
                    id=request.id,
                    result={"registered": True, "workspace_id": ws_id, "path": ws_path},
                )

            if request.method == RpcMethod.BEGIN_OR_RESUME_SESSION:
                ws_id = str(request.params.get("workspace_id", "default"))
                task_id = str(request.params.get("task_id", ""))
                session, cert = self.begin_or_resume_session(ws_id, task_id)
                return RpcResponse(
                    id=request.id,
                    result={
                        "session_id": session.session_id,
                        "state": session.state.value,
                        "task_certificate": cert.to_dict(),
                    },
                )

            if request.method == RpcMethod.EVALUATE_TOOL_CALL:
                ws_id = str(request.params.get("workspace_id", "default"))
                req_data = request.params.get("request", {})
                cap_req = CapabilityRequest.from_dict(req_data)

                # Resolve active task for workspace
                has_active = False
                active_task_id = ""
                for s in self._sessions.values():
                    if s.workspace_id == ws_id and s.state in (
                        SessionState.ACTIVE,
                        SessionState.VERIFYING,
                    ):
                        has_active = True
                        active_task_id = s.task_id
                        break

                context = EnforcementContext(
                    workspace_id=ws_id,
                    has_active_task=has_active,
                    active_task_id=active_task_id,
                    read_only=False,
                )
                decision = self.policy_verifier.evaluate(cap_req, context)

                # Log evaluation event
                session_id = f"sess_{ws_id}_{active_task_id}"
                if session_id in self._event_logs:
                    self._event_logs[session_id].append(
                        "TOOL_EVALUATE",
                        {"request": cap_req.to_dict(), "decision": decision.to_dict()},
                    )

                return RpcResponse(
                    id=request.id,
                    result={"decision": decision.to_dict()},
                )

            return RpcResponse(
                id=request.id,
                error={
                    "code": -32601,
                    "message": f"Method '{request.method.value}' not implemented",
                },
            )

        except Exception as exc:
            return RpcResponse(
                id=request.id,
                error={"code": -32000, "message": str(exc)},
            )

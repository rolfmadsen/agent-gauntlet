"""Portable domain models, RPC contracts, and task session records for Agent Gauntlet Supervisor."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ToolActionType(str, Enum):
    """Tool action classification matching WIT enum definition."""

    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    EXECUTE_COMMAND = "execute_command"
    OTHER = "other"


class DecisionVerdict(str, Enum):
    """Policy decision verdict matching WIT enum definition."""

    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"
    FORCE_ASK = "force_ask"


class SessionState(str, Enum):
    """Explicit task session lifecycle state machine states."""

    DISCOVERED = "DISCOVERED"
    ACTIVE = "ACTIVE"
    VERIFYING = "VERIFYING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    INVALIDATED = "INVALIDATED"
    CLOSED = "CLOSED"


class RpcMethod(str, Enum):
    """Strongly-typed RPC method identifiers exposed by the supervisor daemon."""

    GET_STATUS = "GetStatus"
    REGISTER_WORKSPACE = "RegisterWorkspace"
    BEGIN_OR_RESUME_SESSION = "BeginOrResumeSession"
    EVALUATE_TOOL_CALL = "EvaluateToolCall"
    RECORD_TOOL_RESULT = "RecordToolResult"
    REQUEST_VERIFICATION = "RequestVerification"
    GET_VERIFICATION_STATUS = "GetVerificationStatus"
    CLOSE_SESSION = "CloseSession"


@dataclass(frozen=True)
class CapabilityRequest:
    """Strongly-typed capability request from an agent or adapter."""

    action_type: ToolActionType
    raw_tool_name: str
    target_resource: str
    payload_json: str = "{}"

    def to_dict(self) -> dict[str, Any]:
        """Serializes request to dictionary representation."""
        return {
            "action_type": self.action_type.value,
            "raw_tool_name": self.raw_tool_name,
            "target_resource": self.target_resource,
            "payload_json": self.payload_json,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CapabilityRequest:
        """Constructs CapabilityRequest from dictionary."""
        return cls(
            action_type=ToolActionType(data.get("action_type", "other")),
            raw_tool_name=str(data.get("raw_tool_name", "")),
            target_resource=str(data.get("target_resource", "")),
            payload_json=str(data.get("payload_json", "{}")),
        )


@dataclass(frozen=True)
class EnforcementContext:
    """Immutable trusted context provided by supervisor runtime inspection."""

    workspace_id: str
    has_active_task: bool
    active_task_id: str = ""
    read_only: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serializes context to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnforcementContext:
        """Constructs EnforcementContext from dictionary."""
        return cls(
            workspace_id=str(data.get("workspace_id", "")),
            has_active_task=bool(data.get("has_active_task", False)),
            active_task_id=str(data.get("active_task_id", "")),
            read_only=bool(data.get("read_only", False)),
        )


@dataclass(frozen=True)
class PolicyDecision:
    """Strongly-typed policy decision returned by the verifier."""

    verdict: DecisionVerdict
    reason: str
    reason_code: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serializes decision to dictionary representation."""
        return {
            "verdict": self.verdict.value,
            "reason": self.reason,
            "reason_code": self.reason_code,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PolicyDecision:
        """Constructs PolicyDecision from dictionary."""
        return cls(
            verdict=DecisionVerdict(data.get("verdict", "deny")),
            reason=str(data.get("reason", "")),
            reason_code=int(data.get("reason_code", 0)),
        )


@dataclass(frozen=True)
class TaskSessionRecord:
    """Persistent task session record capturing continuity and state."""

    session_id: str
    workspace_id: str
    task_id: str
    task_digest: str
    state: SessionState = SessionState.DISCOVERED
    snapshot_digest: str = ""
    invalidation_reason: str = ""
    created_at_utc: str = ""
    updated_at_utc: str = ""
    event_count: int = 0
    event_log_root: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serializes session record to dictionary."""
        data = asdict(self)
        data["state"] = self.state.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskSessionRecord:
        """Constructs TaskSessionRecord from dictionary."""
        return cls(
            session_id=str(data.get("session_id", "")),
            workspace_id=str(data.get("workspace_id", "")),
            task_id=str(data.get("task_id", "")),
            task_digest=str(data.get("task_digest", "")),
            state=SessionState(data.get("state", "DISCOVERED")),
            snapshot_digest=str(data.get("snapshot_digest", "")),
            invalidation_reason=str(data.get("invalidation_reason", "")),
            created_at_utc=str(data.get("created_at_utc", "")),
            updated_at_utc=str(data.get("updated_at_utc", "")),
            event_count=int(data.get("event_count", 0)),
            event_log_root=str(data.get("event_log_root", "")),
        )


@dataclass(frozen=True)
class RpcRequest:
    """JSON-RPC request envelope for local supervisor transport."""

    id: str
    method: RpcMethod
    params: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Serializes RPC request to JSON string."""
        return json.dumps(
            {
                "id": self.id,
                "method": self.method.value,
                "params": self.params,
            }
        )

    @classmethod
    def from_json(cls, raw: str) -> RpcRequest:
        """Constructs RpcRequest from JSON string."""
        data = json.loads(raw)
        return cls(
            id=str(data.get("id", "")),
            method=RpcMethod(data.get("method", "GetStatus")),
            params=dict(data.get("params", {})),
        )


@dataclass(frozen=True)
class RpcResponse:
    """JSON-RPC response envelope for local supervisor transport."""

    id: str
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None

    @property
    def is_success(self) -> bool:
        """True if the response represents a successful outcome without error."""
        return self.error is None

    def to_json(self) -> str:
        """Serializes RPC response to JSON string."""
        return json.dumps(
            {
                "id": self.id,
                "result": self.result,
                "error": self.error,
            }
        )

    @classmethod
    def from_json(cls, raw: str) -> RpcResponse:
        """Constructs RpcResponse from JSON string."""
        data = json.loads(raw)
        return cls(
            id=str(data.get("id", "")),
            result=data.get("result"),
            error=data.get("error"),
        )

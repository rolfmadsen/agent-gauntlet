"""Domain models for unsigned verification reports and workspace manifests (Schema v2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class VerificationVerdict(str, Enum):
    """High-level verification outcome."""

    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    INCOMPLETE = "INCOMPLETE"
    SKIPPED = "SKIPPED"


class CheckStatus(str, Enum):
    """Execution status of an individual verification check."""

    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


class ExecutionOrigin(str, Enum):
    """Origin where verification was performed."""

    LOCAL = "LOCAL"
    CI_UNPRIVILEGED = "CI_UNPRIVILEGED"
    CI_PROTECTED = "CI_PROTECTED"


class AttestationStatus(str, Enum):
    """Cryptographic attestation status."""

    ABSENT = "ABSENT"
    VALID = "VALID"
    INVALID = "INVALID"


class TrustDecision(str, Enum):
    """Consumer policy evaluation decision."""

    ACCEPTED = "ACCEPTED"
    POLICY_REJECTED = "POLICY_REJECTED"


@dataclass(frozen=True)
class CheckSummary:
    """Summary of an individual verification check."""

    name: str
    status: str = "PASSED"
    passed: bool = True
    exit_code: int = 0
    duration_seconds: float = 0.0
    optional: bool = False
    log_digest: str = ""

    def __post_init__(self) -> None:
        if not self.passed and self.status == "PASSED":
            object.__setattr__(self, "status", "FAILED")
        elif self.status == "FAILED" and self.passed:
            object.__setattr__(self, "passed", False)


@dataclass(frozen=True)
class TaskContract:
    """Task contract associated with verification run."""

    task_id: str = ""
    task_title: str = ""
    task_digest: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    unresolved_criteria: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class VcsMetadata:
    """Optional VCS metadata captured when Git is available."""

    type: str = "git"
    head: str = ""
    commit: str = ""
    is_dirty: bool = False


@dataclass(frozen=True)
class WorkspaceState:
    """Deterministic workspace state and manifest digests."""

    manifest_version: str = "1.0"
    source_content_digest: str = ""
    source_manifest_digest_pre: str = ""
    source_manifest_digest_post: str = ""
    config_digest: str = ""
    task_digest: str = ""
    policy_digest: str = ""
    check_definitions_digest: str = ""
    included_files_count: int = 0
    vcs: VcsMetadata | None = None


@dataclass(frozen=True)
class ExecutionMetadata:
    """Execution environment and timing metadata."""

    started_at: str = ""
    finished_at: str = ""
    total_duration_seconds: float = 0.0
    environment: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class VerificationReport:
    """Unsigned verification report binding checks to workspace state (Schema v2)."""

    schema_version: str = "2.0.0"
    execution_origin: str = "LOCAL"
    verdict: str = "PASSED"
    task_contract: TaskContract = field(default_factory=TaskContract)
    workspace_state: WorkspaceState = field(default_factory=WorkspaceState)
    execution_metadata: ExecutionMetadata = field(default_factory=ExecutionMetadata)
    checks: list[CheckSummary] = field(default_factory=list)


# Backward compatibility aliases
@dataclass(frozen=True)
class EvidenceRecord:
    """Legacy evidence record (v1) for backward compatibility."""

    task_id: str
    status: str
    source_tree_hash: str
    task_title: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    unresolved_criteria: list[str] = field(default_factory=list)
    checks: list[CheckSummary] = field(default_factory=list)
    timestamp: float = 0.0
    signature: str | None = None

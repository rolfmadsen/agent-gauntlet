"""Evidence and verification reporting feature package for agent-gauntlet."""

from agent_gauntlet.features.evidence.attestation import (
    AttestationBundle,
    AttestationEngine,
    AttestationIdentity,
)
from agent_gauntlet.features.evidence.authority import EvidenceAuthority
from agent_gauntlet.features.evidence.models import (
    AttestationStatus,
    CheckStatus,
    CheckSummary,
    EvidenceRecord,
    ExecutionMetadata,
    ExecutionOrigin,
    TaskContract,
    TrustDecision,
    VcsMetadata,
    VerificationReport,
    VerificationVerdict,
    WorkspaceState,
)
from agent_gauntlet.features.evidence.release_gate import (
    ReleaseReadinessEngine,
    ReleaseReadinessReport,
    check_release_readiness,
)
from agent_gauntlet.features.evidence.report import VerificationReportEngine
from agent_gauntlet.features.evidence.source_state import (
    CanonicalWorkspaceManifest,
    UnicodePathError,
    WorkspaceEscapeError,
    compute_source_state,
    compute_workspace_manifest,
)
from agent_gauntlet.features.evidence.trust_policy import (
    TrustEvaluationResult,
    TrustPolicy,
    TrustPolicyEngine,
)

__all__ = [
    "AttestationBundle",
    "AttestationEngine",
    "AttestationIdentity",
    "AttestationStatus",
    "CanonicalWorkspaceManifest",
    "CheckStatus",
    "CheckSummary",
    "EvidenceAuthority",
    "EvidenceRecord",
    "ExecutionMetadata",
    "ExecutionOrigin",
    "ReleaseReadinessEngine",
    "ReleaseReadinessReport",
    "TaskContract",
    "TrustDecision",
    "TrustEvaluationResult",
    "TrustPolicy",
    "TrustPolicyEngine",
    "UnicodePathError",
    "VcsMetadata",
    "VerificationReport",
    "VerificationReportEngine",
    "VerificationVerdict",
    "WorkspaceEscapeError",
    "WorkspaceState",
    "check_release_readiness",
    "compute_source_state",
    "compute_workspace_manifest",
]

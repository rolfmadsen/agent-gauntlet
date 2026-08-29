"""Deny-by-default Trust Policy model and evaluation engine."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agent_gauntlet.features.evidence.attestation import AttestationBundle
from agent_gauntlet.features.evidence.models import (
    AttestationStatus,
    ExecutionOrigin,
    TrustDecision,
    VerificationReport,
)

ORIGIN_RANKS = {
    ExecutionOrigin.LOCAL.value: 1,
    ExecutionOrigin.CI_UNPRIVILEGED.value: 2,
    ExecutionOrigin.CI_PROTECTED.value: 3,
}


@dataclass(frozen=True)
class TrustPolicy:
    """Consumer security policy governing trusted attestation identities and rules."""

    policy_version: str = "1.0"
    require_attestation: bool = True
    allowed_oidc_issuers: list[str] = field(
        default_factory=lambda: ["https://token.actions.githubusercontent.com"]
    )
    allowed_repositories: list[str] = field(default_factory=list)
    allowed_workflows: list[str] = field(default_factory=list)
    allowed_runner_environments: list[str] = field(default_factory=lambda: ["github-hosted"])
    minimum_origin: ExecutionOrigin = ExecutionOrigin.CI_PROTECTED
    allow_unattested_local_advisory: bool = False


@dataclass(frozen=True)
class TrustEvaluationResult:
    """Orthogonal result of trust policy evaluation."""

    trust_decision: TrustDecision
    release_eligible: bool
    reasons: list[str] = field(default_factory=list)
    evaluated_subject: str = ""
    evaluated_issuer: str = ""


class TrustPolicyEngine:
    """Evaluates verification reports and attestations against a deny-by-default TrustPolicy."""

    def load_policy(self, content_or_path: str | Path | dict[str, Any]) -> TrustPolicy:
        """Loads a TrustPolicy from a file path, JSON string, or dictionary."""
        if isinstance(content_or_path, Path) or (
            isinstance(content_or_path, str) and not content_or_path.strip().startswith("{")
        ):
            path = Path(content_or_path)
            if not path.is_file():
                return TrustPolicy()  # default strict policy
            data = json.loads(path.read_text(encoding="utf-8"))
        elif isinstance(content_or_path, str):
            data = json.loads(content_or_path)
        elif isinstance(content_or_path, dict):
            data = content_or_path
        else:
            return TrustPolicy()

        min_origin_str = str(data.get("minimum_origin", "CI_PROTECTED"))
        try:
            min_origin = ExecutionOrigin(min_origin_str)
        except ValueError:
            min_origin = ExecutionOrigin.CI_PROTECTED

        return TrustPolicy(
            policy_version=str(data.get("policy_version", "1.0")),
            require_attestation=bool(data.get("require_attestation", True)),
            allowed_oidc_issuers=list(
                data.get("allowed_oidc_issuers", ["https://token.actions.githubusercontent.com"])
            ),
            allowed_repositories=list(data.get("allowed_repositories", [])),
            allowed_workflows=list(data.get("allowed_workflows", [])),
            allowed_runner_environments=list(
                data.get("allowed_runner_environments", ["github-hosted"])
            ),
            minimum_origin=min_origin,
            allow_unattested_local_advisory=bool(
                data.get("allow_unattested_local_advisory", False)
            ),
        )

    def evaluate(
        self,
        report: VerificationReport,
        attestation: AttestationBundle | None,
        policy: TrustPolicy,
    ) -> TrustEvaluationResult:
        """
        Evaluates report and optional attestation against policy.
        Release eligibility strictly requires:
          1. report.verdict == PASSED
          2. attestation is VALID (or explicitly overridden by advisory policy)
          3. policy evaluation produces TrustDecision.ACCEPTED
          4. minimum_origin requirement is satisfied
        """
        reasons: list[str] = []
        is_policy_rejected = False

        # 1. Attestation presence and status checks
        if policy.require_attestation:
            if attestation is None:
                reasons.append("Attestation is absent but required by trust policy")
                is_policy_rejected = True
            elif attestation.status != AttestationStatus.VALID:
                reasons.append(f"Attestation status is '{attestation.status}' (expected VALID)")
                is_policy_rejected = True

        # 2. Execution Origin enforcement (derived from verified attestation provenance and report claim)
        has_valid_ci_attestation = (
            attestation is not None
            and attestation.status == AttestationStatus.VALID
            and attestation.identity is not None
            and attestation.identity.issuer in policy.allowed_oidc_issuers
        )
        if (
            report.execution_origin == ExecutionOrigin.CI_PROTECTED.value
            and has_valid_ci_attestation
        ):
            effective_origin = ExecutionOrigin.CI_PROTECTED.value
        elif (
            report.execution_origin == ExecutionOrigin.CI_UNPRIVILEGED.value
            and has_valid_ci_attestation
        ):
            effective_origin = ExecutionOrigin.CI_UNPRIVILEGED.value
        else:
            effective_origin = ExecutionOrigin.LOCAL.value

        effective_origin_rank = ORIGIN_RANKS.get(effective_origin, 1)
        required_origin_rank = ORIGIN_RANKS.get(policy.minimum_origin.value, 3)
        if (
            effective_origin_rank < required_origin_rank
            and not policy.allow_unattested_local_advisory
        ):
            reasons.append(
                f"Execution origin '{effective_origin}' does not satisfy minimum origin '{policy.minimum_origin.value}'"
            )
            is_policy_rejected = True

        # 3. Identity, Issuer, and Runner Environment validation (if attestation present)
        if attestation and attestation.identity:
            identity = attestation.identity
            if identity.issuer not in policy.allowed_oidc_issuers:
                reasons.append(
                    f"OIDC issuer '{identity.issuer}' is not in allowed issuers list: {policy.allowed_oidc_issuers}"
                )
                is_policy_rejected = True

            if (
                policy.allowed_repositories
                and identity.repository not in policy.allowed_repositories
            ):
                reasons.append(
                    f"Repository '{identity.repository}' is not in allowed repositories: {policy.allowed_repositories}"
                )
                is_policy_rejected = True

            if policy.allowed_workflows and identity.workflow not in policy.allowed_workflows:
                reasons.append(
                    f"Workflow '{identity.workflow}' is not in allowed workflows: {policy.allowed_workflows}"
                )
                is_policy_rejected = True

            if (
                policy.allowed_runner_environments
                and identity.runner_environment not in policy.allowed_runner_environments
            ):
                reasons.append(
                    f"Runner environment '{identity.runner_environment}' is not in allowed runner environments: {policy.allowed_runner_environments}"
                )
                is_policy_rejected = True

        # 4. Verdict and Acceptance Criteria check
        if report.verdict != "PASSED":
            reasons.append(f"Verification verdict is '{report.verdict}' (expected 'PASSED')")

        if report.task_contract.unresolved_criteria:
            reasons.append(
                f"Task contract has {len(report.task_contract.unresolved_criteria)} unresolved criteria"
            )

        trust_decision = (
            TrustDecision.POLICY_REJECTED if is_policy_rejected else TrustDecision.ACCEPTED
        )

        has_valid_attestation = (
            attestation is not None and attestation.status == AttestationStatus.VALID
        )
        attestation_satisfied = has_valid_attestation or (
            not policy.require_attestation and policy.allow_unattested_local_advisory
        )

        release_eligible = (
            trust_decision == TrustDecision.ACCEPTED
            and report.verdict == "PASSED"
            and not report.task_contract.unresolved_criteria
            and attestation_satisfied
        )

        return TrustEvaluationResult(
            trust_decision=trust_decision,
            release_eligible=release_eligible,
            reasons=reasons,
            evaluated_subject=attestation.subject_digest if attestation else "",
            evaluated_issuer=attestation.identity.issuer
            if attestation and attestation.identity
            else "",
        )

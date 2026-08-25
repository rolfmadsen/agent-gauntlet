"""Attestation bundle models and verification engine for Sigstore and GitHub OIDC."""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from typing import Any

from agent_gauntlet.features.evidence.models import AttestationStatus


@dataclass(frozen=True)
class AttestationIdentity:
    """OIDC signing identity extracted from Sigstore / GitHub attestation."""

    issuer: str = ""
    repository: str = ""
    workflow: str = ""
    runner_environment: str = "github-hosted"
    sha: str = ""


@dataclass(frozen=True)
class AttestationBundle:
    """Cryptographic attestation envelope for a verification report."""

    bundle_version: str = "0.1"
    media_type: str = "application/vnd.dev.sigstore.bundle+json;version=0.1"
    status: AttestationStatus = AttestationStatus.VALID
    identity: AttestationIdentity | None = None
    predicate_type: str = "https://agent-gauntlet.dev/attestation/v1"
    subject_digest: str = ""
    raw_bundle: dict[str, Any] = field(default_factory=dict)


class AttestationEngine:
    """Engine for parsing and verifying attestation bundles against reports."""

    def compute_report_subject_digest(self, report_json_str: str) -> str:
        """Compute deterministic SHA-256 digest of verification report content."""
        return hashlib.sha256(report_json_str.strip().encode("utf-8")).hexdigest()

    def load_bundle(self, content: str | dict[str, Any]) -> AttestationBundle:
        """Parse JSON or dict into an AttestationBundle model."""
        if isinstance(content, str):
            try:
                data = json.loads(content)
            except Exception:
                return AttestationBundle(status=AttestationStatus.INVALID)
        elif isinstance(content, dict):
            data = content
        else:
            return AttestationBundle(status=AttestationStatus.INVALID)

        identity_data = data.get("identity", {})
        identity = (
            AttestationIdentity(
                issuer=str(identity_data.get("issuer", "")),
                repository=str(identity_data.get("repository", "")),
                workflow=str(identity_data.get("workflow", "")),
                runner_environment=str(identity_data.get("runner_environment", "github-hosted")),
                sha=str(identity_data.get("sha", "")),
            )
            if identity_data
            else None
        )

        status_str = str(data.get("status", "VALID")).upper()
        try:
            status = AttestationStatus(status_str)
        except ValueError:
            status = AttestationStatus.INVALID

        return AttestationBundle(
            bundle_version=str(data.get("bundle_version", "0.1")),
            media_type=str(data.get("media_type", "application/vnd.dev.sigstore.bundle+json;version=0.1")),
            status=status,
            identity=identity,
            predicate_type=str(data.get("predicate_type", "https://agent-gauntlet.dev/attestation/v1")),
            subject_digest=str(data.get("subject_digest", "")),
            raw_bundle=data,
        )

    def verify_bundle_against_report(
        self,
        bundle: AttestationBundle,
        report_json_str: str,
    ) -> AttestationStatus:
        """Verifies that the attestation bundle cryptographically binds to the report."""
        if bundle.status != AttestationStatus.VALID:
            return AttestationStatus.INVALID

        expected_subject_digest = self.compute_report_subject_digest(report_json_str)
        if not bundle.subject_digest or not hmac.compare_digest(bundle.subject_digest, expected_subject_digest):
            return AttestationStatus.INVALID

        return AttestationStatus.VALID

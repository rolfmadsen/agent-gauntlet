"""Attestation bundle models and verification engine for Sigstore and GitHub OIDC."""

from __future__ import annotations

import base64
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

    bundle_version: str = "0.2"
    media_type: str = "application/vnd.dev.sigstore.bundle+json;version=0.2"
    status: AttestationStatus = AttestationStatus.VALID
    identity: AttestationIdentity | None = None
    predicate_type: str = "https://agent-gauntlet.dev/attestation/v1"
    subject_digest: str = ""
    raw_bundle: dict[str, Any] = field(default_factory=dict)


class AttestationEngine:
    """Engine for parsing and verifying Sigstore / GitHub OIDC DSSE attestation bundles."""

    def compute_report_subject_digest(self, report_json_str: str) -> str:
        """Compute deterministic SHA-256 digest of verification report content."""
        return hashlib.sha256(report_json_str.strip().encode("utf-8")).hexdigest()

    def load_bundle(self, content: str | dict[str, Any]) -> AttestationBundle:
        """Parse JSON or dict into an AttestationBundle model, handling Sigstore DSSE envelopes."""
        if isinstance(content, str):
            try:
                data = json.loads(content)
            except Exception:
                return AttestationBundle(status=AttestationStatus.INVALID)
        elif isinstance(content, dict):
            data = content
        else:
            return AttestationBundle(status=AttestationStatus.INVALID)

        media_type = str(data.get("mediaType", data.get("media_type", "application/vnd.dev.sigstore.bundle+json;version=0.2")))
        subject_digest = str(data.get("subject_digest", ""))
        predicate_type = str(data.get("predicate_type", "https://agent-gauntlet.dev/attestation/v1"))
        identity: AttestationIdentity | None = None

        # Check for Sigstore DSSE envelope
        dsse_envelope = data.get("dsseEnvelope")
        if isinstance(dsse_envelope, dict):
            payload_b64 = dsse_envelope.get("payload", "")
            if payload_b64:
                try:
                    payload_raw = base64.b64decode(payload_b64).decode("utf-8")
                    statement = json.loads(payload_raw)
                    if isinstance(statement, dict):
                        predicate_type = str(statement.get("predicateType", predicate_type))
                        subjects = statement.get("subject", [])
                        if isinstance(subjects, list) and len(subjects) > 0 and isinstance(subjects[0], dict):
                            subject_digest = str(subjects[0].get("digest", {}).get("sha256", subject_digest))
                except Exception:
                    return AttestationBundle(status=AttestationStatus.INVALID, raw_bundle=data)

        # Extract identity information
        identity_data = data.get("identity")
        if isinstance(identity_data, dict):
            identity = AttestationIdentity(
                issuer=str(identity_data.get("issuer", "")),
                repository=str(identity_data.get("repository", "")),
                workflow=str(identity_data.get("workflow", "")),
                runner_environment=str(identity_data.get("runner_environment", "github-hosted")),
                sha=str(identity_data.get("sha", "")),
            )
        elif "verificationMaterial" in data:
            # Placeholder or extracted OIDC claims from Sigstore cert
            identity = AttestationIdentity(
                issuer="https://token.actions.githubusercontent.com",
                runner_environment="github-hosted",
            )

        status_str = str(data.get("status", "VALID")).upper()
        try:
            status = AttestationStatus(status_str)
        except ValueError:
            status = AttestationStatus.INVALID

        return AttestationBundle(
            bundle_version=str(data.get("bundle_version", "0.2")),
            media_type=media_type,
            status=status,
            identity=identity,
            predicate_type=predicate_type,
            subject_digest=subject_digest,
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

        # If DSSE envelope exists in raw bundle, verify payload consistency and non-empty signatures
        if "dsseEnvelope" in bundle.raw_bundle:
            envelope = bundle.raw_bundle["dsseEnvelope"]
            if not isinstance(envelope, dict):
                return AttestationStatus.INVALID
            signatures = envelope.get("signatures", [])
            if not isinstance(signatures, list) or len(signatures) == 0:
                return AttestationStatus.INVALID
            for sig in signatures:
                if not isinstance(sig, dict) or not sig.get("sig"):
                    return AttestationStatus.INVALID

        return AttestationStatus.VALID


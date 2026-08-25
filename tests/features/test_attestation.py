"""Unit, acceptance, and invariant tests for TrustPolicy and Cryptographic Sigstore Attestation."""

from __future__ import annotations

import base64
import datetime
import json
import unittest

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import NameOID, ObjectIdentifier

from agent_gauntlet.features.evidence.attestation import (
    AttestationBundle,
    AttestationEngine,
    dsse_pae,
)
from agent_gauntlet.features.evidence.models import (
    AttestationStatus,
    ExecutionOrigin,
    TaskContract,
    TrustDecision,
    VerificationReport,
    WorkspaceState,
)
from agent_gauntlet.features.evidence.report import VerificationReportEngine
from agent_gauntlet.features.evidence.trust_policy import (
    TrustPolicy,
    TrustPolicyEngine,
)


def _generate_crypto_bundle(
    subject_digest: str,
    issuer: str = "https://token.actions.githubusercontent.com",
    repository: str = "rolfmadsen/agent-gauntlet",
    workflow: str = ".github/workflows/ci.yml@refs/heads/main",
    runner_env: str = "github-hosted",
    sha: str = "81d07511cb43efa335d988bd5f0535befda0d8d3",
    tamper_sig: bool = False,
    tamper_payload: bool = False,
) -> dict:
    """Generate a real cryptographically signed Sigstore v0.2 bundle with x509 Fulcio extensions."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    # Build X.509 Certificate with Sigstore/Fulcio OID extensions
    builder = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "agent-gauntlet-ci")]))
        .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Sigstore Fulcio CA")]))
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=5)
        )
        .not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
        )
    )

    # Add Fulcio OID Extensions (Sigstore enterprise arc 1.3.6.1.4.1.57264.1.*)
    builder = builder.add_extension(
        x509.UnrecognizedExtension(
            ObjectIdentifier("1.3.6.1.4.1.57264.1.1"), issuer.encode("utf-8")
        ),
        critical=False,
    )
    builder = builder.add_extension(
        x509.UnrecognizedExtension(
            ObjectIdentifier("1.3.6.1.4.1.57264.1.5"), repository.encode("utf-8")
        ),
        critical=False,
    )
    builder = builder.add_extension(
        x509.UnrecognizedExtension(
            ObjectIdentifier("1.3.6.1.4.1.57264.1.6"), workflow.encode("utf-8")
        ),
        critical=False,
    )
    builder = builder.add_extension(
        x509.UnrecognizedExtension(
            ObjectIdentifier("1.3.6.1.4.1.57264.1.11"), runner_env.encode("utf-8")
        ),
        critical=False,
    )
    builder = builder.add_extension(
        x509.UnrecognizedExtension(ObjectIdentifier("1.3.6.1.4.1.57264.1.3"), sha.encode("utf-8")),
        critical=False,
    )

    cert = builder.sign(private_key, hashes.SHA256())
    cert_der = cert.public_bytes(Encoding.DER)
    cert_b64 = base64.b64encode(cert_der).decode("ascii")

    # Construct in-toto Statement v1
    statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "predicateType": "https://agent-gauntlet.dev/attestation/v1",
        "subject": [
            {
                "name": "verification-report.json",
                "digest": {"sha256": subject_digest},
            }
        ],
        "predicate": {"verdict": "PASSED"},
    }
    payload_raw = json.dumps(statement).encode("utf-8")
    payload_b64 = base64.b64encode(payload_raw).decode("ascii")
    payload_type = "application/vnd.in-toto+json"

    # Pre-Authentication Encoding (PAE)
    pae_bytes = dsse_pae(payload_type, payload_raw)
    signature_bytes = private_key.sign(pae_bytes, ec.ECDSA(hashes.SHA256()))

    if tamper_sig:
        signature_bytes = b"forged_invalid_signature_bytes_that_fail_crypto"
    if tamper_payload:
        tampered_statement = dict(statement)
        tampered_statement["predicate"] = {"verdict": "FAILED", "tampered": True}
        payload_b64 = base64.b64encode(json.dumps(tampered_statement).encode("utf-8")).decode(
            "ascii"
        )

    sig_b64 = base64.b64encode(signature_bytes).decode("ascii")

    return {
        "mediaType": "application/vnd.dev.sigstore.bundle+json;version=0.2",
        "dsseEnvelope": {
            "payload": payload_b64,
            "payloadType": payload_type,
            "signatures": [{"keyid": "k1", "sig": sig_b64}],
        },
        "verificationMaterial": {
            "x509CertificateChain": {
                "certificates": [{"rawBytes": cert_b64}],
            },
            "tlogEntries": [{"logIndex": "12345"}],
        },
    }


class TestAttestationAndTrustPolicy(unittest.TestCase):
    """Tests for orthogonal evaluation of verification result, attestation status, and trust decision."""

    def setUp(self) -> None:
        self.report_engine = VerificationReportEngine()
        self.attestation_engine = AttestationEngine()
        self.trust_engine = TrustPolicyEngine()

        self.passed_report = VerificationReport(
            schema_version="2.0.0",
            execution_origin="CI_PROTECTED",
            verdict="PASSED",
            task_contract=TaskContract(
                task_id="023-p0-audit-remediation", acceptance_criteria=["criterion 1"]
            ),
            workspace_state=WorkspaceState(
                source_manifest_digest_post="abcd1234ef567890abcd1234ef567890abcd1234ef567890abcd1234ef567890"
            ),
        )

        self.failed_report = VerificationReport(
            schema_version="2.0.0",
            execution_origin="CI_PROTECTED",
            verdict="FAILED",
            task_contract=TaskContract(
                task_id="023-p0-audit-remediation", acceptance_criteria=["criterion 1"]
            ),
            workspace_state=WorkspaceState(
                source_manifest_digest_post="abcd1234ef567890abcd1234ef567890abcd1234ef567890abcd1234ef567890"
            ),
        )

        self.local_report = VerificationReport(
            schema_version="2.0.0",
            execution_origin="LOCAL",
            verdict="PASSED",
            task_contract=TaskContract(
                task_id="023-p0-audit-remediation", acceptance_criteria=["criterion 1"]
            ),
            workspace_state=WorkspaceState(
                source_manifest_digest_post="abcd1234ef567890abcd1234ef567890abcd1234ef567890abcd1234ef567890"
            ),
        )

        self.report_json = self.report_engine.generate_report_json(self.passed_report)
        self.report_subject_digest = self.attestation_engine.compute_report_subject_digest(
            self.report_json
        )

        self.valid_bundle_data = _generate_crypto_bundle(self.report_subject_digest)
        self.valid_bundle = self.attestation_engine.load_bundle(self.valid_bundle_data)

        self.strict_policy = TrustPolicy(
            policy_version="1.0",
            require_attestation=True,
            allowed_oidc_issuers=["https://token.actions.githubusercontent.com"],
            allowed_repositories=["rolfmadsen/agent-gauntlet"],
            allowed_workflows=[".github/workflows/ci.yml@refs/heads/main"],
            allowed_runner_environments=["github-hosted"],
            minimum_origin=ExecutionOrigin.CI_PROTECTED,
        )

    def test_cryptographic_dsse_verification_succeeds_for_valid_bundle(self) -> None:
        """P0 Invariant: Cryptographically valid ECDSA DSSE envelope with matching subject returns VALID."""
        self.assertEqual(self.valid_bundle.status, AttestationStatus.VALID)
        self.assertIsNotNone(self.valid_bundle.identity)
        if self.valid_bundle.identity:
            self.assertEqual(
                self.valid_bundle.identity.issuer, "https://token.actions.githubusercontent.com"
            )
            self.assertEqual(self.valid_bundle.identity.repository, "rolfmadsen/agent-gauntlet")
            self.assertEqual(self.valid_bundle.identity.runner_environment, "github-hosted")

        status = self.attestation_engine.verify_bundle_against_report(
            self.valid_bundle, self.report_json
        )
        self.assertEqual(status, AttestationStatus.VALID)

    def test_verify_bundle_rejects_mismatched_report_subject_digest(self) -> None:
        """P0 Invariant: Valid bundle verified against a different report returns INVALID."""
        other_report = self.report_engine.generate_report_json(self.failed_report)
        status = self.attestation_engine.verify_bundle_against_report(
            self.valid_bundle, other_report
        )
        self.assertEqual(status, AttestationStatus.INVALID)

    def test_cryptographic_dsse_verification_rejects_mock_or_forged_signature(self) -> None:
        """P0 Invariant: Mock signature bytes or invalid cryptographic signatures return INVALID."""
        mock_bundle_data = _generate_crypto_bundle(self.report_subject_digest, tamper_sig=True)
        bundle = self.attestation_engine.load_bundle(mock_bundle_data)
        status = self.attestation_engine.verify_bundle_against_report(bundle, self.report_json)
        self.assertEqual(status, AttestationStatus.INVALID)

    def test_cryptographic_dsse_verification_rejects_tampered_payload(self) -> None:
        """P0 Invariant: Tampering with payload bytes after signing breaks signature and returns INVALID."""
        tampered_bundle_data = _generate_crypto_bundle(
            self.report_subject_digest, tamper_payload=True
        )
        bundle = self.attestation_engine.load_bundle(tampered_bundle_data)
        status = self.attestation_engine.verify_bundle_against_report(bundle, self.report_json)
        self.assertEqual(status, AttestationStatus.INVALID)

    def test_valid_attestation_and_passed_verdict_yields_accepted_release(self) -> None:
        """P0 Invariant: PASSED + VALID attestation + ACCEPTED policy = release_eligible."""
        eval_result = self.trust_engine.evaluate(
            report=self.passed_report,
            attestation=self.valid_bundle,
            policy=self.strict_policy,
        )
        self.assertEqual(eval_result.trust_decision, TrustDecision.ACCEPTED)
        self.assertTrue(eval_result.release_eligible)
        self.assertEqual(len(eval_result.reasons), 0)

    def test_minimum_origin_enforcement_rejects_local_report_under_ci_protected_policy(
        self,
    ) -> None:
        """P0 Invariant: LOCAL execution origin is rejected under minimum_origin=CI_PROTECTED."""
        eval_result = self.trust_engine.evaluate(
            report=self.local_report,
            attestation=self.valid_bundle,
            policy=self.strict_policy,
        )
        self.assertEqual(eval_result.trust_decision, TrustDecision.POLICY_REJECTED)
        self.assertFalse(eval_result.release_eligible)
        self.assertTrue(any("origin" in r.lower() for r in eval_result.reasons))

    def test_runner_environment_enforcement_rejects_unauthorized_runner(self) -> None:
        """P0 Invariant: Self-hosted runner is rejected when allowed_runner_environments=['github-hosted']."""
        self_hosted_bundle_data = _generate_crypto_bundle(
            self.report_subject_digest, runner_env="self-hosted"
        )
        bundle = self.attestation_engine.load_bundle(self_hosted_bundle_data)
        eval_result = self.trust_engine.evaluate(
            report=self.passed_report,
            attestation=bundle,
            policy=self.strict_policy,
        )
        self.assertEqual(eval_result.trust_decision, TrustDecision.POLICY_REJECTED)
        self.assertFalse(eval_result.release_eligible)
        self.assertTrue(any("runner" in r.lower() for r in eval_result.reasons))

    def test_valid_attestation_on_failed_verdict_preserves_valid_status_but_rejects_release(
        self,
    ) -> None:
        """P0 Invariant: Attestation status remains VALID for signed failures, but release is rejected."""
        eval_result = self.trust_engine.evaluate(
            report=self.failed_report,
            attestation=self.valid_bundle,
            policy=self.strict_policy,
        )
        self.assertEqual(eval_result.trust_decision, TrustDecision.ACCEPTED)
        self.assertFalse(eval_result.release_eligible)
        self.assertTrue(any("failed" in r.lower() for r in eval_result.reasons))

    def test_untrusted_issuer_is_policy_rejected(self) -> None:
        """P0 Invariant: Rogue OIDC issuer is rejected with POLICY_REJECTED."""
        rogue_bundle_data = _generate_crypto_bundle(
            self.report_subject_digest, issuer="https://evil-issuer.com"
        )
        rogue_bundle = self.attestation_engine.load_bundle(rogue_bundle_data)
        eval_result = self.trust_engine.evaluate(
            report=self.passed_report,
            attestation=rogue_bundle,
            policy=self.strict_policy,
        )
        self.assertEqual(eval_result.trust_decision, TrustDecision.POLICY_REJECTED)
        self.assertFalse(eval_result.release_eligible)
        self.assertTrue(any("issuer" in r.lower() for r in eval_result.reasons))

    def test_untrusted_repository_is_policy_rejected(self) -> None:
        """P0 Invariant: Valid token from unauthorized fork repository is rejected."""
        fork_bundle_data = _generate_crypto_bundle(
            self.report_subject_digest, repository="attacker/forked-agent-gauntlet"
        )
        fork_bundle = self.attestation_engine.load_bundle(fork_bundle_data)
        eval_result = self.trust_engine.evaluate(
            report=self.passed_report,
            attestation=fork_bundle,
            policy=self.strict_policy,
        )
        self.assertEqual(eval_result.trust_decision, TrustDecision.POLICY_REJECTED)
        self.assertFalse(eval_result.release_eligible)
        self.assertTrue(any("repository" in r.lower() for r in eval_result.reasons))

    def test_invalid_attestation_status_is_policy_rejected(self) -> None:
        """P0 Invariant: Attestation with status INVALID is strictly rejected with POLICY_REJECTED."""
        invalid_bundle = AttestationBundle(
            bundle_version=self.valid_bundle.bundle_version,
            status=AttestationStatus.INVALID,
            identity=self.valid_bundle.identity,
            subject_digest=self.valid_bundle.subject_digest,
        )
        eval_result = self.trust_engine.evaluate(
            report=self.passed_report,
            attestation=invalid_bundle,
            policy=self.strict_policy,
        )
        self.assertEqual(eval_result.trust_decision, TrustDecision.POLICY_REJECTED)
        self.assertFalse(eval_result.release_eligible)
        self.assertTrue(any("invalid" in r.lower() for r in eval_result.reasons))


if __name__ == "__main__":
    unittest.main()

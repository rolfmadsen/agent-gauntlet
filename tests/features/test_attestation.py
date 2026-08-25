"""Unit, acceptance, and invariant tests for TrustPolicy and Attestation verification."""

import json
import unittest

from agent_gauntlet.features.evidence.attestation import (
    AttestationBundle,
    AttestationEngine,
    AttestationIdentity,
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
            task_contract=TaskContract(task_id="021-trust-genesis"),
            workspace_state=WorkspaceState(
                source_manifest_digest_post="abcd1234ef567890abcd1234ef567890abcd1234ef567890abcd1234ef567890"
            ),
        )

        self.failed_report = VerificationReport(
            schema_version="2.0.0",
            execution_origin="CI_PROTECTED",
            verdict="FAILED",
            task_contract=TaskContract(task_id="021-trust-genesis"),
            workspace_state=WorkspaceState(
                source_manifest_digest_post="abcd1234ef567890abcd1234ef567890abcd1234ef567890abcd1234ef567890"
            ),
        )

        self.report_json = self.report_engine.generate_report_json(self.passed_report)
        self.report_subject_digest = self.attestation_engine.compute_report_subject_digest(self.report_json)

        self.valid_identity = AttestationIdentity(
            issuer="https://token.actions.githubusercontent.com",
            repository="rolfmadsen/agent-gauntlet",
            workflow=".github/workflows/ci.yml@refs/heads/main",
            runner_environment="github-hosted",
            sha="e2341ad",
        )

        self.valid_bundle = AttestationBundle(
            bundle_version="0.1",
            status=AttestationStatus.VALID,
            identity=self.valid_identity,
            subject_digest=self.report_subject_digest,
        )

        self.strict_policy = TrustPolicy(
            policy_version="1.0",
            require_attestation=True,
            allowed_oidc_issuers=["https://token.actions.githubusercontent.com"],
            allowed_repositories=["rolfmadsen/agent-gauntlet"],
            allowed_workflows=[".github/workflows/ci.yml@refs/heads/main"],
            minimum_origin=ExecutionOrigin.CI_PROTECTED,
        )

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

    def test_valid_attestation_on_failed_verdict_preserves_valid_status_but_rejects_release(self) -> None:
        """P0 Invariant: Attestation status remains VALID for signed failures, but release is rejected."""
        eval_result = self.trust_engine.evaluate(
            report=self.failed_report,
            attestation=self.valid_bundle,
            policy=self.strict_policy,
        )
        self.assertEqual(
            eval_result.trust_decision,
            TrustDecision.ACCEPTED,
            "Signed failure from valid identity is trusted as an authentic failure report",
        )
        self.assertFalse(
            eval_result.release_eligible,
            "Failed verdict must never be eligible for release/stabilization",
        )
        self.assertTrue(
            any("failed" in r.lower() for r in eval_result.reasons),
            "Failed verdict reason must be present",
        )

    def test_untrusted_issuer_is_policy_rejected(self) -> None:
        """P0 Invariant: Unknown or spoofed OIDC issuer is rejected with POLICY_REJECTED."""
        rogue_identity = AttestationIdentity(
            issuer="https://evil-issuer.com",
            repository="rolfmadsen/agent-gauntlet",
            workflow=".github/workflows/ci.yml@refs/heads/main",
        )
        rogue_bundle = AttestationBundle(
            status=AttestationStatus.VALID,
            identity=rogue_identity,
            subject_digest=self.report_subject_digest,
        )

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
        fork_identity = AttestationIdentity(
            issuer="https://token.actions.githubusercontent.com",
            repository="attacker/forked-agent-gauntlet",
            workflow=".github/workflows/ci.yml@refs/heads/main",
        )
        fork_bundle = AttestationBundle(
            status=AttestationStatus.VALID,
            identity=fork_identity,
            subject_digest=self.report_subject_digest,
        )

        eval_result = self.trust_engine.evaluate(
            report=self.passed_report,
            attestation=fork_bundle,
            policy=self.strict_policy,
        )
        self.assertEqual(eval_result.trust_decision, TrustDecision.POLICY_REJECTED)
        self.assertFalse(eval_result.release_eligible)
        self.assertTrue(any("repository" in r.lower() for r in eval_result.reasons))

    def test_invalid_attestation_status_is_policy_rejected(self) -> None:
        """P0 Invariant: Attestation with status INVALID is rejected with POLICY_REJECTED."""
        invalid_bundle = AttestationBundle(
            status=AttestationStatus.INVALID,
            identity=self.valid_identity,
            subject_digest=self.report_subject_digest,
        )
        eval_result = self.trust_engine.evaluate(
            report=self.passed_report,
            attestation=invalid_bundle,
            policy=self.strict_policy,
        )
        self.assertEqual(eval_result.trust_decision, TrustDecision.POLICY_REJECTED)
        self.assertFalse(eval_result.release_eligible)
        self.assertTrue(any("invalid" in r.lower() for r in eval_result.reasons))

    def test_absent_attestation_fails_when_required(self) -> None:
        """P0 Invariant: Absent attestation fails policy when require_attestation=True."""
        eval_result = self.trust_engine.evaluate(
            report=self.passed_report,
            attestation=None,
            policy=self.strict_policy,
        )
        self.assertEqual(eval_result.trust_decision, TrustDecision.POLICY_REJECTED)
        self.assertFalse(eval_result.release_eligible)
        self.assertTrue(any("absent" in r.lower() for r in eval_result.reasons))

    def test_attestation_bundle_subject_mismatch_fails_verification(self) -> None:
        """P0 Invariant: Subject digest mismatch returns AttestationStatus.INVALID."""
        status = self.attestation_engine.verify_bundle_against_report(
            bundle=self.valid_bundle,
            report_json_str=json.dumps({"modified": True}),
        )
        self.assertEqual(status, AttestationStatus.INVALID)

    def test_sigstore_dsse_envelope_parsing_and_verification(self) -> None:
        """P0 Invariant: Sigstore Bundle v0.2 DSSE envelope is parsed, decoded, and validated."""
        import base64
        statement = {
            "_type": "https://in-toto.io/Statement/v1",
            "predicateType": "https://agent-gauntlet.dev/attestation/v1",
            "subject": [
                {
                    "name": "verification-report.json",
                    "digest": {"sha256": self.report_subject_digest},
                }
            ],
            "predicate": {"verdict": "PASSED"},
        }
        payload_b64 = base64.b64encode(json.dumps(statement).encode("utf-8")).decode("utf-8")
        sigstore_bundle = {
            "mediaType": "application/vnd.dev.sigstore.bundle+json;version=0.2",
            "dsseEnvelope": {
                "payload": payload_b64,
                "payloadType": "application/vnd.in-toto+json",
                "signatures": [{"keyid": "k1", "sig": "valid_mock_signature_bytes"}],
            },
            "verificationMaterial": {
                "tlogEntries": [{"logIndex": "12345"}],
            },
        }
        bundle = self.attestation_engine.load_bundle(sigstore_bundle)
        self.assertEqual(bundle.subject_digest, self.report_subject_digest)
        self.assertEqual(bundle.predicate_type, "https://agent-gauntlet.dev/attestation/v1")

        status = self.attestation_engine.verify_bundle_against_report(bundle, self.report_json)
        self.assertEqual(status, AttestationStatus.VALID)

    def test_sigstore_dsse_fabricated_signature_rejected(self) -> None:
        """P0 Invariant: DSSE envelope with empty signatures is rejected as INVALID."""
        import base64
        statement = {
            "_type": "https://in-toto.io/Statement/v1",
            "subject": [{"digest": {"sha256": self.report_subject_digest}}],
        }
        payload_b64 = base64.b64encode(json.dumps(statement).encode("utf-8")).decode("utf-8")
        fabricated_bundle = {
            "mediaType": "application/vnd.dev.sigstore.bundle+json;version=0.2",
            "dsseEnvelope": {
                "payload": payload_b64,
                "payloadType": "application/vnd.in-toto+json",
                "signatures": [],  # Fabricated / empty signatures
            },
        }
        bundle = self.attestation_engine.load_bundle(fabricated_bundle)
        status = self.attestation_engine.verify_bundle_against_report(bundle, self.report_json)
        self.assertEqual(status, AttestationStatus.INVALID)


if __name__ == "__main__":
    unittest.main()


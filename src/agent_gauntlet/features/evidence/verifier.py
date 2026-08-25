"""Evidence and attestation verification execution engine."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TextIO

from agent_gauntlet.features.evidence.attestation import (
    AttestationBundle,
    AttestationEngine,
)
from agent_gauntlet.features.evidence.models import (
    AttestationStatus,
)
from agent_gauntlet.features.evidence.report import VerificationReportEngine
from agent_gauntlet.features.evidence.source_state import compute_workspace_manifest
from agent_gauntlet.features.evidence.trust_policy import (
    TrustPolicyEngine,
)


def execute_check_evidence(
    workspace: Path,
    evidence_file: str = "",
    legacy_advisory: bool = False,
    as_json: bool = False,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Checks verification report integrity, criteria resolution, check outcomes, and workspace state."""
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr

    engine = VerificationReportEngine()
    target_file = evidence_file
    if not target_file:
        if (workspace / "verification-report.json").is_file():
            target_file = "verification-report.json"
        elif (workspace / "evidence.json").is_file():
            target_file = "evidence.json"
        else:
            target_file = "verification-report.json"

    evidence_path = (
        workspace / target_file if not Path(target_file).is_absolute() else Path(target_file)
    )
    if not evidence_path.is_file():
        print(f"FAILED: Evidence file '{evidence_path}' does not exist.", file=err)
        return 1

    try:
        raw_content = evidence_path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"FAILED: Failed to parse evidence file '{evidence_path}': {exc}", file=err)
        return 1

    classification = engine.classify_evidence_payload(raw_content)
    if classification == "LEGACY_UNATTESTED":
        if not legacy_advisory:
            print(
                "FAILED: Legacy v1 HMAC evidence detected. Legacy evidence cannot satisfy authoritative verification gates. "
                "Re-run 'agent-gauntlet verify' to produce an unsigned v2 verification report, or pass --legacy-advisory for local advisory inspection.",
                file=err,
            )
            return 1
        else:
            print(
                f"[LEGACY_UNATTESTED] Legacy evidence in '{evidence_path}' inspected in advisory mode.",
                file=out,
            )
            return 0

    try:
        report_obj = engine.load_report_json(raw_content)
    except Exception as exc:
        print(f"FAILED: Failed to parse verification report '{evidence_path}': {exc}", file=err)
        return 1

    if report_obj.verdict != "PASSED":
        print(
            f"FAILED: Verification report records non-passed verdict: '{report_obj.verdict}'.",
            file=err,
        )
        return 1

    if report_obj.task_contract.unresolved_criteria:
        print(
            f"FAILED: Verification report has {len(report_obj.task_contract.unresolved_criteria)} unresolved acceptance criteria.",
            file=err,
        )
        return 1

    failed_checks = [
        c
        for c in report_obj.checks
        if not c.optional and (not c.passed or c.exit_code != 0 or c.status == "FAILED")
    ]
    if failed_checks:
        print(
            f"FAILED: Verification report contains {len(failed_checks)} failed check(s): {[c.name for c in failed_checks]}.",
            file=err,
        )
        return 1

    current_manifest = compute_workspace_manifest(workspace)
    if not engine.verify_workspace_state_match(
        report_obj,
        current_manifest.source_manifest_digest,
        current_manifest.policy_digest,
        current_manifest.config_digest,
    ):
        report_digest = report_obj.workspace_state.source_manifest_digest_post or "(none)"
        print(
            f"FAILED: Source manifest or policy drift detected! Report bound to '{report_digest}', but current workspace is '{current_manifest.source_manifest_digest}'.",
            file=err,
        )
        return 1

    if as_json:
        print(
            json.dumps(
                {"status": "VALID", "report": json.loads(engine.generate_report_json(report_obj))},
                indent=2,
            ),
            file=out,
        )
    else:
        print(
            f"[VALID] Source manifest verified ({current_manifest.source_manifest_digest[:16]}) [origin: {report_obj.execution_origin}, attestation: ABSENT].",
            file=out,
        )
    return 0


def execute_check_attestation(
    workspace: Path,
    report_file: str,
    attestation_file: str = "",
    policy_file: str = "",
    allow_unattested: bool = False,
    as_json: bool = False,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Checks verification report and cryptographic DSSE attestation against consumer TrustPolicy."""
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr

    report_path = Path(report_file)
    if not report_path.is_absolute():
        report_path = (workspace / report_path).resolve()

    if not report_path.is_file():
        print(f"FAILED: Verification report '{report_path}' not found.", file=err)
        return 1

    raw_report = report_path.read_text(encoding="utf-8")
    report_engine = VerificationReportEngine()
    try:
        report_obj = report_engine.load_report_json(raw_report)
    except Exception as exc:
        print(f"FAILED: Failed to parse verification report '{report_path}': {exc}", file=err)
        return 1

    current_manifest = compute_workspace_manifest(workspace)
    if not report_engine.verify_workspace_state_match(
        report_obj,
        current_manifest.source_manifest_digest,
        current_manifest.policy_digest,
        current_manifest.config_digest,
    ):
        report_digest = report_obj.workspace_state.source_manifest_digest_post or "(none)"
        print(
            f"FAILED: Source manifest or policy drift detected! Report bound to '{report_digest}', but current workspace is '{current_manifest.source_manifest_digest}'.",
            file=err,
        )
        return 1

    # Load Attestation bundle if provided / present
    attestation_bundle: AttestationBundle | None = None
    attestation_engine = AttestationEngine()
    attestation_path_str = attestation_file
    if not attestation_path_str and (workspace / "attestation.json").is_file():
        attestation_path_str = str(workspace / "attestation.json")

    if attestation_path_str:
        att_path = Path(attestation_path_str)
        if not att_path.is_absolute():
            att_path = (workspace / att_path).resolve()
        if att_path.is_file():
            raw_bundle = att_path.read_text(encoding="utf-8")
            bundle = attestation_engine.load_bundle(raw_bundle)
            status = attestation_engine.verify_bundle_against_report(bundle, raw_report)
            if status != AttestationStatus.VALID:
                attestation_bundle = AttestationBundle(
                    bundle_version=bundle.bundle_version,
                    status=AttestationStatus.INVALID,
                    identity=bundle.identity,
                    subject_digest=bundle.subject_digest,
                )
            else:
                attestation_bundle = bundle

    # Load TrustPolicy
    trust_engine = TrustPolicyEngine()
    policy_path_str = policy_file
    if not policy_path_str and (workspace / ".agent-gauntlet/trust-policy.json").is_file():
        policy_path_str = str(workspace / ".agent-gauntlet/trust-policy.json")

    if policy_path_str:
        p_path = Path(policy_path_str)
        if not p_path.is_absolute():
            p_path = (workspace / p_path).resolve()
        trust_policy = trust_engine.load_policy(p_path)
    else:
        trust_policy = trust_engine.load_policy({})

    evaluation_result = trust_engine.evaluate(
        report=report_obj,
        attestation=attestation_bundle,
        policy=trust_policy,
    )

    attestation_status_val = (
        attestation_bundle.status.value if attestation_bundle else AttestationStatus.ABSENT.value
    )
    verification_result_val = report_obj.verdict
    trust_decision_val = evaluation_result.trust_decision.value
    release_eligible = evaluation_result.release_eligible

    if allow_unattested and attestation_status_val == AttestationStatus.ABSENT.value:
        is_success = (
            report_obj.verdict == "PASSED" and not report_obj.task_contract.unresolved_criteria
        )
    else:
        is_success = release_eligible

    if as_json:
        result_payload = {
            "verification_result": verification_result_val,
            "attestation_status": attestation_status_val,
            "trust_decision": trust_decision_val,
            "release_eligible": release_eligible,
            "reasons": evaluation_result.reasons,
            "subject_digest": evaluation_result.evaluated_subject,
            "issuer": evaluation_result.evaluated_issuer,
        }
        print(json.dumps(result_payload, indent=2), file=out)
    else:
        print("\nAttestation & Trust Evaluation:", file=out)
        print(f"  Verification Result:  {verification_result_val}", file=out)
        print(f"  Attestation Status:   {attestation_status_val}", file=out)
        print(f"  Trust Decision:       {trust_decision_val}", file=out)
        print(f"  Release Eligible:     {'YES' if release_eligible else 'NO'}", file=out)
        if evaluation_result.reasons:
            print("\nEvaluation Details / Reasons:", file=out)
            for r in evaluation_result.reasons:
                print(f"  [!] {r}", file=err if not is_success else out)

    return 0 if is_success else 1

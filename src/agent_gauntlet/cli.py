"""Command-line interface for agent-gauntlet multi-stack verification engine."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from agent_gauntlet.features.adapters import SUPPORTED_HARNESSES, get_adapter
from agent_gauntlet.features.config.loader import (
    load_config,
)
from agent_gauntlet.features.diagnostics.parser import DiagnosticParser
from agent_gauntlet.features.evidence.attestation import (
    AttestationBundle,
    AttestationEngine,
)
from agent_gauntlet.features.evidence.models import (
    AttestationStatus,
    CheckSummary,
    ExecutionMetadata,
    TaskContract,
    VerificationReport,
    WorkspaceState,
)
from agent_gauntlet.features.evidence.report import VerificationReportEngine
from agent_gauntlet.features.evidence.source_state import (
    compute_source_state,
    compute_workspace_manifest,
)
from agent_gauntlet.features.evidence.trust_policy import (
    TrustPolicy,
    TrustPolicyEngine,
)
from agent_gauntlet.features.gauntlet.models import LayerDefinition, LayerRequirement
from agent_gauntlet.features.gauntlet.runner import run_gauntlet
from agent_gauntlet.features.hooks.gatekeeper import is_task_active
from agent_gauntlet.features.okf.stamper import stamp_okf_file
from agent_gauntlet.features.okf.validator import (
    validate_okf_workspace,
)
from agent_gauntlet.features.scaffold.scaffolder import ProjectScaffolder
from agent_gauntlet.features.stacks.profiles import SUPPORTED_STACKS


def _resolve_task_contract(
    workspace: Path, explicit_task_id: str = ""
) -> tuple[str, str, list[str], list[str]]:
    """
    Finds and parses task contract from tasks/.
    Returns (task_id, task_title, acceptance_criteria, unresolved_criteria).
    """
    tasks_dir = workspace / "tasks"
    if not tasks_dir.is_dir():
        return explicit_task_id or "default-run", "", [], []

    target_file: Path | None = None

    if explicit_task_id and explicit_task_id != "gauntlet-run":
        for candidate in sorted(tasks_dir.glob("*.md")):
            if (
                candidate.stem == explicit_task_id
                or candidate.name == explicit_task_id
                or candidate.name.startswith(f"{explicit_task_id}-")
                or candidate.stem.startswith(explicit_task_id)
            ):
                target_file = candidate
                break

    if not target_file:
        for candidate in sorted(tasks_dir.glob("*.md")):
            try:
                content = candidate.read_text(encoding="utf-8")
                if is_task_active(content):
                    target_file = candidate
                    break
            except Exception:
                continue

    if not target_file:
        return explicit_task_id or "default-run", "", [], []

    try:
        content = target_file.read_text(encoding="utf-8")
    except Exception:
        return explicit_task_id or target_file.stem, "", [], []

    task_id = target_file.stem
    task_title = ""
    acceptance_criteria: list[str] = []
    unresolved_criteria: list[str] = []

    for line in content.splitlines():
        line_strip = line.strip()
        if not task_title and line_strip.startswith("# "):
            task_title = line_strip[2:].strip()
        elif line_strip.startswith("- [ ]") or line_strip.startswith("* [ ]"):
            item = line_strip[5:].strip()
            acceptance_criteria.append(item)
            unresolved_criteria.append(item)
        elif (
            line_strip.startswith("- [x]")
            or line_strip.startswith("- [X]")
            or line_strip.startswith("* [x]")
            or line_strip.startswith("* [X]")
        ):
            item = line_strip[5:].strip()
            acceptance_criteria.append(item)

    return task_id, task_title, acceptance_criteria, unresolved_criteria


def _generate_session_handoff_prompt(
    workspace: Path, task_id: str, task_title: str = ""
) -> str:
    """Generates a clean starter prompt for the next chat session."""
    tasks_dir = workspace / "tasks"
    next_task_suggestion = ""
    if tasks_dir.is_dir():
        for candidate in sorted(tasks_dir.glob("*.md")):
            if candidate.stem != task_id and not candidate.name.startswith(f"{task_id}-"):
                try:
                    content = candidate.read_text(encoding="utf-8")
                    if is_task_active(content):
                        next_task_suggestion = f" (f.eks. tasks/{candidate.name})"
                        break
                except Exception:
                    continue

    return (
        f"Fortsæt udviklingen i projektet. Læs venligst CONTEXT.md, docs/adr/ og den næste opgave i tasks/{next_task_suggestion} "
        f"for at fastlægge acceptkriterier og køre TDD-cyklussen for næste feature."
    )


def main(argv: list[str] | None = None) -> int:
    """Entry point for agent-gauntlet CLI."""
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "-w",
        "--workspace",
        default=".",
        help="Workspace root path (default: current directory)",
    )
    common_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )

    parser = argparse.ArgumentParser(
        prog="agent-gauntlet",
        description="High-assurance multi-stack verification engine and actionable diagnostics harness",
        parents=[common_parser],
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. init
    init_parser = subparsers.add_parser(
        "init",
        help="Generate default gauntlet.toml configuration for workspace",
        parents=[common_parser],
    )
    init_parser.add_argument(
        "--stack",
        choices=SUPPORTED_STACKS,
        default=None,
        help="Target programming stack (default: auto-detect)",
    )
    init_parser.add_argument(
        "--format",
        choices=["toml", "json"],
        default="toml",
        help="Configuration format (default: toml)",
    )
    init_parser.add_argument(
        "--harness",
        choices=SUPPORTED_HARNESSES,
        default="antigravity",
        help="Target agent harness profile (default: antigravity)",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing configuration file",
    )

    # 2. validate-plugin
    validate_plugin_parser = subparsers.add_parser(
        "validate-plugin",
        help="Mechanically validate adapter plugin structure, manifest, skills, and hooks",
        parents=[common_parser],
    )
    validate_plugin_parser.add_argument(
        "--plugin-dir",
        default="plugins/agent-gauntlet",
        help="Path to plugin directory (default: plugins/agent-gauntlet)",
    )
    validate_plugin_parser.add_argument(
        "--harness",
        choices=SUPPORTED_HARNESSES,
        default="antigravity",
        help="Target harness type (default: antigravity)",
    )

    # 3. tree-hash
    subparsers.add_parser(
        "tree-hash",
        help="Compute SHA-256 source tree hash of workspace",
        parents=[common_parser],
    )

    # 4. check-evidence
    check_parser = subparsers.add_parser(
        "check-evidence",
        help="Verify workspace source manifest against verification report and check status",
        parents=[common_parser],
    )
    check_parser.add_argument(
        "--evidence-file",
        default="",
        help="Path to verification report or evidence JSON file (default: verification-report.json or evidence.json)",
    )
    check_parser.add_argument(
        "--legacy-advisory",
        action="store_true",
        help="Allow inspection of legacy v1 evidence records in advisory mode",
    )

    # 5. verify
    verify_parser = subparsers.add_parser(
        "verify",
        help="Execute complete verification gauntlet and generate unsigned verification report",
        parents=[common_parser],
    )
    verify_parser.add_argument(
        "--stack",
        choices=SUPPORTED_STACKS,
        default=None,
        help="Override stack profile for verification",
    )
    verify_parser.add_argument(
        "--task-id",
        default="gauntlet-run",
        help="Identifier for the task or run being verified",
    )
    verify_parser.add_argument(
        "--test-target",
        default="",
        help="Specific test file or pattern to narrow test layer execution",
    )
    verify_parser.add_argument(
        "--diagnostics-json",
        action="store_true",
        help="Output structured Actionable Diagnostics JSON for AI feedback loops",
    )
    verify_parser.add_argument(
        "--standalone",
        action="store_true",
        help="Run verification without requiring CONTEXT.md or an active task in tasks/",
    )
    verify_parser.add_argument(
        "--save",
        action="store_true",
        default=True,
        help="Persist evidence.json and evidence.md upon completion",
    )

    # 5. okf
    okf_parser = subparsers.add_parser(
        "okf",
        help="Validate and stamp Open Knowledge Format (OKF v0.2) markdown documentation",
        parents=[common_parser],
    )
    okf_subparsers = okf_parser.add_subparsers(dest="okf_subcommand", required=True)

    okf_validate_parser = okf_subparsers.add_parser(
        "validate",
        help="Validate OKF v0.2 frontmatter and temporal/actor invariants across markdown files",
        parents=[common_parser],
    )
    okf_validate_parser.add_argument(
        "paths",
        nargs="*",
        default=[],
        help="Target files or directories to validate (default: tasks/, docs/adr/, spec.md, CONTEXT.md)",
    )

    okf_stamp_parser = okf_subparsers.add_parser(
        "stamp",
        help="Stamp or update OKF v0.2 frontmatter in a markdown document",
        parents=[common_parser],
    )
    okf_stamp_parser.add_argument("file", help="Path to markdown file to stamp")
    okf_stamp_parser.add_argument("--type", dest="doc_type", default=None, help="Concept type")
    okf_stamp_parser.add_argument(
        "--status",
        choices=["draft", "stable", "deprecated"],
        default=None,
        help="Lifecycle status",
    )
    okf_stamp_parser.add_argument(
        "--verified-by", default=None, help="Actor who verified this doc (e.g. human:developer)"
    )
    okf_stamp_parser.add_argument(
        "--verified-at", default=None, help="ISO 8601 UTC timestamp of verification"
    )
    okf_stamp_parser.add_argument(
        "--generated-by", default=None, help="Actor who generated this doc"
    )
    okf_stamp_parser.add_argument(
        "--generated-at", default=None, help="ISO 8601 UTC timestamp of generation"
    )
    okf_stamp_parser.add_argument("--title", default=None, help="Display title")

    # 6. check-attestation
    attest_parser = subparsers.add_parser(
        "check-attestation",
        help="Verify detached cryptographic attestation and evaluate deny-by-default TrustPolicy",
        parents=[common_parser],
    )
    attest_parser.add_argument(
        "--report",
        "-r",
        default="verification-report.json",
        help="Path to verification report JSON (default: verification-report.json)",
    )
    attest_parser.add_argument(
        "--attestation",
        "-a",
        default="",
        help="Path to Sigstore / GitHub attestation bundle JSON",
    )
    attest_parser.add_argument(
        "--trust-policy",
        "-p",
        default="",
        help="Path to TrustPolicy JSON configuration (default: .agent-gauntlet/trust-policy.json or built-in strict policy)",
    )
    attest_parser.add_argument(
        "--allow-unattested",
        action="store_true",
        help="Permit unattested local reports in advisory mode (ineligible for release/stabilization)",
    )

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if isinstance(exc.code, int):
            return exc.code
        return 0 if exc.code is None else 1

    workspace = Path(args.workspace).resolve()

    # --- Command: init ---
    if args.command == "init":
        scaffolder = ProjectScaffolder()
        result = scaffolder.scaffold(
            workspace=workspace,
            stack=args.stack,
            harness=args.harness,
            config_format=args.format,
            force=args.force,
        )

        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(f"Scaffolded agent-gauntlet workspace for stack '{result.stack}' and harness '{result.harness}':")
            for entry in result.entries:
                try:
                    rel = Path(entry.path).relative_to(workspace)
                except ValueError:
                    rel = entry.path
                tag = (
                    "[+]"
                    if entry.status.value == "CREATED"
                    else ("[*]" if entry.status.value == "OVERWRITTEN" else "[-]")
                )
                print(f"  {tag} {entry.status.value:11} {rel} ({entry.description})")
        return 0

    # --- Command: validate-plugin ---
    if args.command == "validate-plugin":
        adapter = get_adapter(args.harness)
        target_dir = Path(args.plugin_dir)
        if not target_dir.is_absolute():
            target_dir = (workspace / target_dir).resolve()

        res = adapter.validate_plugin(target_dir)
        if args.json:
            print(
                json.dumps(
                    {
                        "valid": res.valid,
                        "plugin_dir": str(target_dir),
                        "harness": args.harness,
                        "issues": [
                            {"severity": i.severity.value, "path": i.path, "message": i.message}
                            for i in res.issues
                        ],
                    },
                    indent=2,
                )
            )
        else:
            status_label = "VALID" if res.valid else "INVALID"
            print(f"[{status_label}] Plugin validation for '{target_dir}' ({args.harness}):")
            if not res.issues:
                print("  [+] Manifest, skills, and hooks are intact and valid.")
            else:
                for issue in res.issues:
                    tag = "[!]" if issue.severity.value == "ERROR" else "[*]"
                    print(f"  {tag} {issue.severity.value} ({issue.path}): {issue.message}")
        return 0 if res.valid else 1

    # --- Command: tree-hash ---
    if args.command == "tree-hash":
        head, commit, tree = compute_source_state(workspace)
        if args.json:
            print(json.dumps({"head": head, "source_commit": commit, "source_tree_hash": tree}, indent=2))
        else:
            print(tree)
        return 0

    # --- Command: check-evidence ---
    if args.command == "check-evidence":
        engine = VerificationReportEngine()
        target_file = args.evidence_file
        if not target_file:
            if (workspace / "verification-report.json").is_file():
                target_file = "verification-report.json"
            elif (workspace / "evidence.json").is_file():
                target_file = "evidence.json"
            else:
                target_file = "verification-report.json"

        evidence_path = workspace / target_file if not Path(target_file).is_absolute() else Path(target_file)
        if not evidence_path.is_file():
            print(f"FAILED: Evidence file '{evidence_path}' does not exist.", file=sys.stderr)
            return 1

        try:
            raw_content = evidence_path.read_text(encoding="utf-8")
        except Exception as exc:
            print(f"FAILED: Failed to parse evidence file '{evidence_path}': {exc}", file=sys.stderr)
            return 1

        classification = engine.classify_evidence_payload(raw_content)
        if classification == "LEGACY_UNATTESTED":
            if not args.legacy_advisory:
                print(
                    "FAILED: Legacy v1 HMAC evidence detected. Legacy evidence cannot satisfy authoritative verification gates. "
                    "Re-run 'agent-gauntlet verify' to produce an unsigned v2 verification report, or pass --legacy-advisory for local advisory inspection.",
                    file=sys.stderr,
                )
                return 1
            else:
                print(f"[LEGACY_UNATTESTED] Legacy evidence in '{evidence_path}' inspected in advisory mode.")
                return 0

        try:
            report_obj = engine.load_report_json(raw_content)
        except Exception as exc:
            print(f"FAILED: Failed to parse verification report '{evidence_path}': {exc}", file=sys.stderr)
            return 1

        if report_obj.verdict != "PASSED":
            print(f"FAILED: Verification report records non-passed verdict: '{report_obj.verdict}'.", file=sys.stderr)
            return 1

        if report_obj.task_contract.unresolved_criteria:
            print(
                f"FAILED: Verification report has {len(report_obj.task_contract.unresolved_criteria)} unresolved acceptance criteria.",
                file=sys.stderr,
            )
            return 1

        failed_checks = [
            c for c in report_obj.checks
            if not c.optional and (not c.passed or c.exit_code != 0 or c.status == "FAILED")
        ]
        if failed_checks:
            print(
                f"FAILED: Verification report contains {len(failed_checks)} failed check(s): {[c.name for c in failed_checks]}.",
                file=sys.stderr,
            )
            return 1

        current_manifest = compute_workspace_manifest(workspace)
        if not engine.verify_workspace_state_match(report_obj, current_manifest.source_manifest_digest):
            report_digest = report_obj.workspace_state.source_manifest_digest_post or "(none)"
            print(
                f"FAILED: Source manifest drift detected! Report bound to '{report_digest}', but current workspace is '{current_manifest.source_manifest_digest}'.",
                file=sys.stderr,
            )
            return 1

        if args.json:
            print(json.dumps({"status": "VALID", "report": json.loads(engine.generate_report_json(report_obj))}, indent=2))
        else:
            print(f"[VALID] Source manifest verified ({current_manifest.source_manifest_digest[:16]}) [origin: {report_obj.execution_origin}, attestation: ABSENT].")
        return 0

    # --- Command: check-attestation ---
    if args.command == "check-attestation":
        report_path = Path(args.report)
        if not report_path.is_absolute():
            report_path = (workspace / report_path).resolve()

        if not report_path.is_file():
            print(f"FAILED: Verification report '{report_path}' not found.", file=sys.stderr)
            return 1

        raw_report = report_path.read_text(encoding="utf-8")
        report_engine = VerificationReportEngine()
        try:
            report_obj = report_engine.load_report_json(raw_report)
        except Exception as exc:
            print(f"FAILED: Failed to parse verification report '{report_path}': {exc}", file=sys.stderr)
            return 1

        current_manifest = compute_workspace_manifest(workspace)
        if not report_engine.verify_workspace_state_match(report_obj, current_manifest.source_manifest_digest):
            report_digest = report_obj.workspace_state.source_manifest_digest_post or "(none)"
            print(
                f"FAILED: Source manifest drift detected! Report bound to '{report_digest}', but current workspace is '{current_manifest.source_manifest_digest}'.",
                file=sys.stderr,
            )
            return 1

        # Load Attestation bundle if provided / present
        attestation_bundle: AttestationBundle | None = None
        attestation_engine = AttestationEngine()
        attestation_path_str = args.attestation
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
        policy_path_str = args.trust_policy
        if not policy_path_str and (workspace / ".agent-gauntlet/trust-policy.json").is_file():
            policy_path_str = str(workspace / ".agent-gauntlet/trust-policy.json")

        trust_policy = trust_engine.load_policy(policy_path_str) if policy_path_str else TrustPolicy()

        # Evaluate orthogonal dimensions
        eval_result = trust_engine.evaluate(
            report=report_obj,
            attestation=attestation_bundle,
            policy=trust_policy,
        )

        attestation_status_val = (
            attestation_bundle.status.value if attestation_bundle else AttestationStatus.ABSENT.value
        )
        verification_result_val = report_obj.verdict
        trust_decision_val = eval_result.trust_decision.value
        release_eligible = eval_result.release_eligible

        if args.allow_unattested and attestation_status_val == AttestationStatus.ABSENT.value:
            is_success = report_obj.verdict == "PASSED" and not report_obj.task_contract.unresolved_criteria
        else:
            is_success = release_eligible

        if args.json:
            out_data = {
                "verification_result": verification_result_val,
                "attestation_status": attestation_status_val,
                "trust_decision": trust_decision_val,
                "release_eligible": release_eligible,
                "reasons": eval_result.reasons,
                "subject_digest": eval_result.evaluated_subject,
                "issuer": eval_result.evaluated_issuer,
            }
            print(json.dumps(out_data, indent=2))
        else:
            print("\nAttestation & Trust Evaluation:")
            print(f"  Verification Result:  {verification_result_val}")
            print(f"  Attestation Status:   {attestation_status_val}")
            print(f"  Trust Decision:       {trust_decision_val}")
            print(f"  Release Eligible:     {'YES' if release_eligible else 'NO'}")
            if eval_result.reasons:
                print("\nEvaluation Details / Reasons:")
                for r in eval_result.reasons:
                    print(f"  [!] {r}")

        return 0 if is_success else 1

    # --- Command: okf ---
    if args.command == "okf":
        if args.okf_subcommand == "validate":
            targets = args.paths if args.paths else None
            report = validate_okf_workspace(workspace, target_paths=targets)

            if args.json:
                print(
                    json.dumps(
                        {
                            "valid": report.valid,
                            "total_files": report.total_files,
                            "valid_files": report.valid_files,
                            "findings": [
                                {
                                    "file_path": f.file_path,
                                    "rule": f.rule,
                                    "message": f.message,
                                    "remediation_hint": f.remediation_hint,
                                    "severity": f.severity,
                                }
                                for f in report.findings
                            ],
                        },
                        indent=2,
                    )
                )
            else:
                tag = "[VALID]" if report.valid else "[INVALID]"
                print(f"{tag} OKF v0.2 validation: {report.valid_files}/{report.total_files} files compliant.")
                if report.findings:
                    print("\nOKF Findings:")
                    for f in report.findings:
                        try:
                            rel_p = Path(f.file_path).relative_to(workspace)
                        except ValueError:
                            rel_p = f.file_path
                        print(f"  [!] {f.rule} in {rel_p}")
                        print(f"      Message: {f.message}")
                        if f.remediation_hint:
                            print(f"      Hint:    {f.remediation_hint}")

            return 0 if report.valid else 1

        if args.okf_subcommand == "stamp":
            target_file = Path(args.file)
            if not target_file.is_absolute():
                target_file = (workspace / target_file).resolve()

            if not target_file.is_file():
                print(f"FAILED: File '{target_file}' does not exist.", file=sys.stderr)
                return 1

            stamp_okf_file(
                file_path=target_file,
                doc_type=args.doc_type,
                status=args.status,
                verified_by=args.verified_by,
                verified_at=args.verified_at,
                generated_by=args.generated_by,
                generated_at=args.generated_at,
                title=args.title,
            )
            if args.json:
                print(json.dumps({"status": "STAMPED", "file": str(target_file)}, indent=2))
            else:
                try:
                    rel_p = target_file.relative_to(workspace)
                except ValueError:
                    rel_p = target_file
                print(f"[+] Stamped OKF frontmatter in {rel_p}")
            return 0

    # --- Command: verify ---
    if args.command == "verify":
        start_time = time.time()
        started_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        manifest_pre = compute_workspace_manifest(workspace)
        config = load_config(workspace, explicit_stack=args.stack)

        task_id, task_title, criteria, unresolved = _resolve_task_contract(workspace, args.task_id)

        if not args.standalone and not args.test_target:
            context_file = workspace / "CONTEXT.md"
            if not context_file.exists() or not context_file.read_text(encoding="utf-8").strip():
                print("FAILED: Pre-flight check failed! CONTEXT.md is missing or empty. Please define domain glossary in CONTEXT.md or use --standalone.")
                return 1

            okf_report = validate_okf_workspace(workspace)
            if not okf_report.valid:
                print(f"FAILED: Pre-flight OKF validation failed! {len(okf_report.findings)} documentation defect(s) found:")
                for f in okf_report.findings[:5]:
                    try:
                        rel_p = Path(f.file_path).relative_to(workspace)
                    except ValueError:
                        rel_p = f.file_path
                    print(f"  [!] {f.rule} in {rel_p}: {f.message}")
                    if f.remediation_hint:
                        print(f"      Hint: {f.remediation_hint}")
                if len(okf_report.findings) > 5:
                    print(f"  ... and {len(okf_report.findings) - 5} more defect(s). Run 'agent-gauntlet okf validate' for full report.")
                return 1

        layers: list[LayerDefinition] = []
        if args.test_target:
            layers.append(
                LayerDefinition(
                    name="targeted-test",
                    command=[sys.executable, "-m", "unittest", args.test_target],
                    optional=False,
                )
            )
        else:
            layers = config.to_layer_definitions()

        report = run_gauntlet(layers, cwd=workspace)
        finished_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        total_duration = time.time() - start_time
        manifest_post = compute_workspace_manifest(workspace)

        diagnostic_parser = DiagnosticParser()
        diagnostic_reports = [
            diagnostic_parser.parse_layer_output(
                layer_name=res.name,
                command=layers[i].command if i < len(layers) else [res.name],
                exit_code=res.exit_code,
                output=res.output,
            )
            for i, res in enumerate(report.layers)
        ]

        checks = [
            CheckSummary(
                name=layer.name,
                status="PASSED" if layer.passed else "FAILED",
                passed=layer.passed,
                exit_code=layer.exit_code,
                duration_seconds=layer.duration_seconds,
                optional=(layer.requirement == LayerRequirement.OPTIONAL),
            )
            for layer in report.layers
        ]

        task_contract = TaskContract(
            task_id=task_id,
            task_title=task_title,
            task_digest=manifest_post.task_digest,
            acceptance_criteria=criteria,
            unresolved_criteria=unresolved,
        )

        workspace_state = WorkspaceState(
            manifest_version="1.0",
            source_content_digest=manifest_post.source_content_digest,
            source_manifest_digest_pre=manifest_pre.source_manifest_digest,
            source_manifest_digest_post=manifest_post.source_manifest_digest,
            config_digest=manifest_post.config_digest,
            task_digest=manifest_post.task_digest,
            policy_digest=manifest_post.policy_digest,
            included_files_count=manifest_post.included_files_count,
            vcs=manifest_post.vcs,
        )

        exec_metadata = ExecutionMetadata(
            started_at=started_iso,
            finished_at=finished_iso,
            total_duration_seconds=total_duration,
            environment={
                "python_version": sys.version.split()[0],
                "platform": sys.platform,
                "gauntlet_version": "0.2.0",
            },
        )

        if report.success:
            if args.test_target:
                verdict = "PARTIAL"
            elif unresolved:
                verdict = "INCOMPLETE"
            else:
                verdict = "PASSED"
        else:
            verdict = "FAILED"

        report_obj = VerificationReport(
            schema_version="2.0.0",
            execution_origin="LOCAL",
            verdict=verdict,
            task_contract=task_contract,
            workspace_state=workspace_state,
            execution_metadata=exec_metadata,
            checks=checks,
        )

        engine = VerificationReportEngine()
        if args.save:
            report_json_str = engine.generate_report_json(report_obj)
            (workspace / "verification-report.json").write_text(report_json_str, encoding="utf-8")
            (workspace / config.evidence_file).write_text(report_json_str, encoding="utf-8")
            (workspace / config.evidence_markdown_file).write_text(
                engine.generate_report_markdown(report_obj), encoding="utf-8"
            )
            # ZERO SELF-MUTATION: Do NOT mutate tasks/*.md during verify

        handoff_prompt = (
            _generate_session_handoff_prompt(
                workspace,
                report_obj.task_contract.task_id,
                report_obj.task_contract.task_title,
            )
            if verdict == "PASSED"
            else ""
        )

        tree_digest = manifest_post.source_manifest_digest[:16]
        is_verify_success = verdict == "PASSED" or (verdict == "PARTIAL" and report.success)

        if args.diagnostics_json:
            output_payload = {
                "verdict": verdict,
                "source_tree_hash": tree_digest,
                "execution_origin": "LOCAL",
                "diagnostic_reports": [r.to_dict() for r in diagnostic_reports],
                "handoff_prompt": handoff_prompt,
            }
            print(json.dumps(output_payload, indent=2))
        elif args.json:
            print(engine.generate_report_json(report_obj))
        else:
            print(f"\nVerification Result: {verdict}")
            if report_obj.task_contract.task_id and report_obj.task_contract.task_id != "default-run":
                task_label = (
                    f"{report_obj.task_contract.task_id} ({report_obj.task_contract.task_title})"
                    if report_obj.task_contract.task_title
                    else report_obj.task_contract.task_id
                )
                print(f"Bound Task:          {task_label}")
            print(f"Stack Profile:       {config.stack}")
            print(f"Source Tree Hash:    {tree_digest}")
            print("Execution Origin:    LOCAL (Unsigned report)")
            print("\nVerification Layers:")
            for c in report_obj.checks:
                tag = "[+]" if c.passed else "[-]"
                print(f"  {tag} {c.name} (exit {c.exit_code}) in {c.duration_seconds:.3f}s")

            all_findings = [f for r in diagnostic_reports for f in r.findings]
            if all_findings:
                print("\nActionable Diagnostics:")
                for f in all_findings:
                    location = f"{f.file_path}:{f.line_number}" if f.file_path and f.line_number else (f.file_path or f.tool_name)
                    print(f"  [!] {f.finding_type.value} in {location}")
                    print(f"      Message: {f.message}")
                    if f.remediation_hint:
                        print(f"      Hint:    {f.remediation_hint}")

            if verdict == "PASSED" and handoff_prompt:
                import textwrap

                print("\n" + "╭" + "─" * 76 + "╮")
                print(f"│ 🏁 SESSION HANDOFF: {report_obj.task_contract.task_id:<53} │")
                print("│" + " " * 76 + "│")
                print("│ 💡 Start venligst en frisk chat-session for at undgå context rot.          │")
                print("│ 📋 Kopiér og indsæt følgende starter-prompt i en ny chat:                  │")
                print("├" + "─" * 76 + "┤")
                for wrapped_line in textwrap.wrap(handoff_prompt, width=74):
                    print(f"│ {wrapped_line:<74} │")
                print("╰" + "─" * 76 + "╯")

        return 0 if is_verify_success else 1

    return 2



if __name__ == "__main__":
    raise SystemExit(main())

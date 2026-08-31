"""Command-line interface for agent-gauntlet multi-stack verification engine."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agent_gauntlet.features.adapters import SUPPORTED_HARNESSES, get_adapter
from agent_gauntlet.features.doctor.checker import DoctorChecker
from agent_gauntlet.features.evidence.source_state import compute_source_state
from agent_gauntlet.features.evidence.verifier import (
    execute_check_attestation,
    execute_check_evidence,
    execute_check_release,
    execute_check_spec,
    execute_verify,
)
from agent_gauntlet.features.okf.stamper import stamp_okf_file
from agent_gauntlet.features.okf.validator import validate_okf_workspace
from agent_gauntlet.features.scaffold.scaffolder import ProjectScaffolder
from agent_gauntlet.features.stacks.profiles import SUPPORTED_STACKS


def _handle_scaffold_op(args: argparse.Namespace, workspace: Path, op: str) -> int:
    """Dispatches scaffold/init operations through ProjectScaffolder."""
    res = ProjectScaffolder().scaffold(
        workspace=workspace,
        stack=args.stack,
        harness=args.harness,
        config_format=args.format,
        force=args.force,
    )
    if args.json:
        print(json.dumps(res.to_dict(), indent=2))
        return 0
    verb = "Initialized" if op == "init" else "Scaffolded"
    stack_label = ", ".join(res.stacks) if res.stacks else res.stack
    print(f"{verb} agent-gauntlet for '{stack_label}' and '{res.harness}':")
    for e in res.entries:
        try:
            rel = Path(e.path).relative_to(workspace)
        except ValueError:
            rel = e.path
        tag = (
            "[+]"
            if e.status.value == "CREATED"
            else ("[*]" if e.status.value == "OVERWRITTEN" else "[-]")
        )
        print(f"  {tag} {e.status.value:11} {rel}")
    return 0


def _handle_doctor(args: argparse.Namespace, workspace: Path) -> int:
    """Dispatches workspace integrity and duplicate diagnostics."""
    report = DoctorChecker().check_workspace(workspace)
    print(json.dumps(report.to_dict(), indent=2) if args.json else report.format_terminal())
    return 0 if not report.has_errors else 1


def _handle_validate_plugin(args: argparse.Namespace, workspace: Path) -> int:
    """Dispatches plugin validation against harness adapter."""
    target = Path(args.plugin_dir)
    target_dir = target if target.is_absolute() else (workspace / target).resolve()
    res = get_adapter(args.harness).validate_plugin(target_dir)
    if args.json:
        issues = [
            {"severity": i.severity.value, "path": i.path, "message": i.message} for i in res.issues
        ]
        print(
            json.dumps(
                {
                    "valid": res.valid,
                    "plugin_dir": str(target_dir),
                    "harness": args.harness,
                    "issues": issues,
                },
                indent=2,
            )
        )
    else:
        status_label = "VALID" if res.valid else "INVALID"
        print(f"[{status_label}] Plugin validation for '{target_dir}' ({args.harness}):")
        if not res.issues:
            print("  [+] Manifest, skills, and hooks are intact and valid.")
        for i in res.issues:
            tag = "[!]" if i.severity.value == "ERROR" else "[*]"
            print(f"  {tag} {i.severity.value} ({i.path}): {i.message}")
    return 0 if res.valid else 1


def _handle_okf(args: argparse.Namespace, workspace: Path) -> int:
    """Dispatches OKF frontmatter validation and stamping subcommands."""
    if args.okf_subcommand == "validate":
        rep = validate_okf_workspace(workspace, target_paths=args.paths if args.paths else None)
        if args.json:
            findings = [
                {
                    "file_path": f.file_path,
                    "rule": f.rule,
                    "message": f.message,
                    "remediation_hint": f.remediation_hint,
                    "severity": f.severity,
                }
                for f in rep.findings
            ]
            print(
                json.dumps(
                    {
                        "valid": rep.valid,
                        "total_files": rep.total_files,
                        "valid_files": rep.valid_files,
                        "findings": findings,
                    },
                    indent=2,
                )
            )
        else:
            tag = "[VALID]" if rep.valid else "[INVALID]"
            print(
                f"{tag} OKF v0.2 validation: {rep.valid_files}/{rep.total_files} files compliant."
            )
            for f in rep.findings:
                try:
                    rel_p = Path(f.file_path).relative_to(workspace)
                except ValueError:
                    rel_p = f.file_path
                print(f"  [!] {f.rule} in {rel_p}\n      Message: {f.message}")
                if f.remediation_hint:
                    print(f"      Hint:    {f.remediation_hint}")
        return 0 if rep.valid else 1

    if args.okf_subcommand == "stamp":
        tf = Path(args.file)
        target_file = tf if tf.is_absolute() else (workspace / tf).resolve()
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
    return 2


def build_cli_parser() -> argparse.ArgumentParser:
    """Build and configure the CLI ArgumentParser."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-w", "--workspace", default=".", help="Workspace root path")
    common.add_argument("--json", action="store_true", help="Output results as JSON")

    parser = argparse.ArgumentParser(
        prog="agent-gauntlet", description="Multi-stack verification engine", parents=[common]
    )
    subs = parser.add_subparsers(dest="command", required=True)

    for cmd in ["init", "scaffold"]:
        sp = subs.add_parser(cmd, parents=[common])
        sp.add_argument("-s", "--stack", "--stacks", dest="stack", help="Target stack(s)")
        sp.add_argument("--harness", choices=SUPPORTED_HARNESSES, default="antigravity")
        sp.add_argument("-f", "--format", choices=["toml", "json"], default="toml")
        sp.add_argument("--force", action="store_true")

    subs.add_parser("doctor", parents=[common])
    val_p = subs.add_parser("validate-plugin", parents=[common])
    val_p.add_argument("-p", "--plugin-dir", default=".agents")
    val_p.add_argument("--harness", choices=SUPPORTED_HARNESSES, default="antigravity")
    subs.add_parser("tree-hash", parents=[common])

    chk_ev = subs.add_parser("check-evidence", parents=[common])
    chk_ev.add_argument("-e", "--evidence-file", default="")
    chk_ev.add_argument("--legacy-advisory", action="store_true")

    chk_rel = subs.add_parser("check-release", parents=[common])
    chk_rel.add_argument(
        "--allow-unreleased", action="store_true", help="Allow [Unreleased] changelog"
    )

    chk_att = subs.add_parser("check-attestation", parents=[common])
    chk_att.add_argument("-r", "--report", default="verification-report.json")
    chk_att.add_argument("-a", "--attestation", default="")
    chk_att.add_argument("-p", "--trust-policy", default="")
    chk_att.add_argument("--allow-unattested", action="store_true")

    chk_spec = subs.add_parser("check-spec", parents=[common])
    chk_spec.add_argument("-t", "--task", dest="task_id", default="")
    chk_spec.add_argument("--all", dest="check_all", action="store_true")

    okf_p = subs.add_parser("okf", parents=[common])
    okf_sub = okf_p.add_subparsers(dest="okf_subcommand", required=True)
    okf_val = okf_sub.add_parser("validate", parents=[common])
    okf_val.add_argument("paths", nargs="*", default=[])
    okf_st = okf_sub.add_parser("stamp", parents=[common])
    okf_st.add_argument("file")
    okf_st.add_argument("-t", "--type", dest="doc_type", required=True)
    okf_st.add_argument(
        "-s",
        "--status",
        required=True,
        choices=["draft", "active", "stable", "superseded", "deprecated", "rejected"],
    )
    okf_st.add_argument("--title", default="")
    okf_st.add_argument("--verified-by", default="")
    okf_st.add_argument("--verified-at", default="")
    okf_st.add_argument("--generated-by", default="")
    okf_st.add_argument("--generated-at", default="")

    v_p = subs.add_parser("verify", parents=[common])
    v_p.add_argument("-s", "--stack", choices=SUPPORTED_STACKS)
    v_p.add_argument("-t", "--task-id", default="")
    v_p.add_argument("--test-target", default="")
    v_p.add_argument("--standalone", action="store_true")
    v_p.add_argument("--save", action="store_true", default=True)
    v_p.add_argument("--no-save", dest="save", action="store_false")
    v_p.add_argument("--diagnostics-json", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for agent-gauntlet CLI."""
    args = build_cli_parser().parse_args(argv)
    workspace = Path(args.workspace).resolve()

    if args.command in ("init", "scaffold"):
        return _handle_scaffold_op(args, workspace, args.command)
    if args.command == "doctor":
        return _handle_doctor(args, workspace)
    if args.command == "validate-plugin":
        return _handle_validate_plugin(args, workspace)
    if args.command == "tree-hash":
        head, commit, tree = compute_source_state(workspace)
        print(
            json.dumps({"head": head, "source_commit": commit, "source_tree_hash": tree}, indent=2)
            if args.json
            else tree
        )
        return 0
    if args.command == "check-evidence":
        return execute_check_evidence(
            workspace, args.evidence_file, args.legacy_advisory, args.json
        )
    if args.command == "check-release":
        return execute_check_release(
            workspace, allow_unreleased=args.allow_unreleased, as_json=args.json
        )
    if args.command == "check-spec":
        return execute_check_spec(
            workspace, task_id=args.task_id, check_all=args.check_all, as_json=args.json
        )
    if args.command == "check-attestation":
        return execute_check_attestation(
            workspace,
            args.report,
            args.attestation,
            args.trust_policy,
            args.allow_unattested,
            args.json,
        )
    if args.command == "okf":
        return _handle_okf(args, workspace)
    if args.command == "verify":
        return execute_verify(
            workspace=workspace,
            task_id=args.task_id,
            stack=args.stack or "",
            standalone=args.standalone,
            test_target=args.test_target,
            save=args.save,
            as_json=args.json,
            diagnostics_json=args.diagnostics_json,
        )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

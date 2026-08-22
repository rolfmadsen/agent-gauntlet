"""Command-line interface for agent-gauntlet multi-stack verification engine."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from agent_gauntlet.features.config.loader import (
    generate_default_config_json,
    generate_default_config_toml,
    load_config,
)
from agent_gauntlet.features.diagnostics.parser import DiagnosticParser
from agent_gauntlet.features.evidence.authority import EvidenceAuthority
from agent_gauntlet.features.evidence.models import CheckSummary, EvidenceRecord
from agent_gauntlet.features.gauntlet.models import LayerDefinition
from agent_gauntlet.features.gauntlet.runner import run_gauntlet
from agent_gauntlet.features.scaffold.scaffolder import ProjectScaffolder
from agent_gauntlet.features.stacks.detector import detect_stack
from agent_gauntlet.features.stacks.profiles import SUPPORTED_STACKS
from agent_gauntlet.features.evidence.source_state import compute_source_state


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
                if "status" in content.lower() and "done" not in content.lower().split("status")[1][:40]:
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
        "--force",
        action="store_true",
        help="Overwrite existing configuration file",
    )

    # 2. tree-hash
    subparsers.add_parser(
        "tree-hash",
        help="Compute SHA-256 source tree hash of workspace",
        parents=[common_parser],
    )

    # 3. check-evidence
    check_parser = subparsers.add_parser(
        "check-evidence",
        help="Verify HMAC signature and tree-hash match of evidence ledger",
        parents=[common_parser],
    )
    check_parser.add_argument(
        "--evidence-file",
        default="evidence.json",
        help="Path to evidence JSON file (default: evidence.json)",
    )

    # 4. verify
    verify_parser = subparsers.add_parser(
        "verify",
        help="Execute complete verification gauntlet and generate signed evidence",
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

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code

    workspace = Path(args.workspace).resolve()
    authority = EvidenceAuthority()

    # --- Command: init ---
    if args.command == "init":
        scaffolder = ProjectScaffolder()
        result = scaffolder.scaffold(
            workspace=workspace,
            stack=args.stack,
            config_format=args.format,
            force=args.force,
        )

        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(f"Scaffolded agent-gauntlet workspace for stack profile '{result.stack}':")
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
        evidence_path = workspace / args.evidence_file
        if not evidence_path.is_file():
            print(f"FAILED: Evidence file '{evidence_path}' does not exist.", file=sys.stderr)
            return 1

        try:
            record = authority.load_evidence_json(evidence_path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"FAILED: Failed to parse evidence file '{evidence_path}': {exc}", file=sys.stderr)
            return 1

        if not authority.verify_record(record):
            print("FAILED: Evidence signature is invalid or has been tampered with.", file=sys.stderr)
            return 1

        head, commit, current_tree = compute_source_state(workspace)
        if not authority.verify_source_state_match(record, current_tree):
            print(
                f"FAILED: Source tree drift detected! Evidence bound to '{record.source_tree_hash}', but current workspace is '{current_tree}'.",
                file=sys.stderr,
            )
            return 1

        if args.json:
            print(json.dumps({"status": "VALID", "record": json.loads(authority.generate_evidence_json(record))}, indent=2))
        else:
            print(f"[VALID] Evidence signature verified ({record.signature[:16]}...) and matches current source tree ({current_tree}).")
        return 0

    # --- Command: verify ---
    if args.command == "verify":
        head, commit, tree = compute_source_state(workspace)
        config = load_config(workspace, explicit_stack=args.stack)

        task_id, task_title, criteria, unresolved = _resolve_task_contract(workspace, args.task_id)

        if not args.standalone and not args.test_target:
            context_file = workspace / "CONTEXT.md"
            if not context_file.exists() or not context_file.read_text(encoding="utf-8").strip():
                print("FAILED: Pre-flight check failed! CONTEXT.md is missing or empty. Please define domain glossary in CONTEXT.md or use --standalone.")
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
                name=l.name,
                passed=l.passed,
                exit_code=l.exit_code,
                duration_seconds=l.duration_seconds,
            )
            for l in report.layers
        ]

        record = EvidenceRecord(
            task_id=task_id,
            task_title=task_title,
            acceptance_criteria=criteria,
            unresolved_criteria=unresolved,
            status="PASSED" if report.success else "FAILED",
            source_tree_hash=tree,
            checks=checks,
            timestamp=time.time(),
        )
        signed_record = authority.sign_record(record)

        if args.save:
            (workspace / config.evidence_file).write_text(authority.generate_evidence_json(signed_record))
            (workspace / config.evidence_markdown_file).write_text(
                authority.generate_evidence_markdown(signed_record, head=head, source_commit=commit)
            )

        if args.diagnostics_json:
            output_payload = {
                "verdict": "PASSED" if report.success else "FAILED",
                "source_tree_hash": tree,
                "signature": signed_record.signature,
                "diagnostic_reports": [r.to_dict() for r in diagnostic_reports],
            }
            print(json.dumps(output_payload, indent=2))
        elif args.json:
            print(authority.generate_evidence_json(signed_record))
        else:
            verdict = "PASSED" if report.success else "FAILED"
            print(f"\nVerification Result: {verdict}")
            if signed_record.task_id and signed_record.task_id != "default-run":
                task_label = f"{signed_record.task_id} ({signed_record.task_title})" if signed_record.task_title else signed_record.task_id
                print(f"Bound Task:          {task_label}")
            print(f"Stack Profile:       {config.stack}")
            print(f"Source Tree Hash:    {tree}")
            print(f"Signature:           {signed_record.signature}")
            print("\nVerification Layers:")
            for c in signed_record.checks:
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

        return 0 if report.success else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())

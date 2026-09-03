"""CLI command handler for OKF frontmatter validation and stamping."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agent_gauntlet.features.okf.stamper import stamp_okf_file
from agent_gauntlet.features.okf.validator import validate_okf_workspace


def execute_okf_cli(args: argparse.Namespace, workspace: Path) -> int:
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
            print(f"FAILED: File '{target_file}' does not exist.", file=sys.stderr, flush=True)
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

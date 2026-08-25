"""CLI PreInvocation Hook entrypoint for Google Antigravity IDE."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import TextIO

from agent_gauntlet.features.adapters.antigravity.adapter import AntigravityAdapter


def main_hook_entrypoint(
    argv: list[str] | None = None,
    stdin: TextIO = sys.stdin,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
    workspace: Path | None = None,
) -> int:
    """PreInvocation / PreToolUse hook CLI handler for Antigravity IDE."""
    active_workspace = workspace or Path(os.getcwd()).resolve()

    try:
        content = stdin.read().strip()
        if not content:
            output_payload = {"decision": "deny", "reason": "Empty payload received on stdin."}
            stdout.write(json.dumps(output_payload) + "\n")
            stderr.write("\n🛑 Gatekeeper: Empty payload received on stdin.\n")
            return 1
        payload = json.loads(content)
    except Exception as exc:
        output_payload = {"decision": "deny", "reason": f"Corrupt JSON payload on stdin: {exc}"}
        stdout.write(json.dumps(output_payload) + "\n")
        stderr.write(f"\n🛑 Gatekeeper: Corrupt JSON payload on stdin: {exc}\n")
        return 1

    adapter = AntigravityAdapter()
    verdict = adapter.evaluate_invocation(workspace=active_workspace, payload=payload)

    if not verdict.allowed:
        output_payload = {"decision": "deny", "reason": verdict.reason}
        stdout.write(json.dumps(output_payload) + "\n")
        stderr.write(f"\n{verdict.reason}\n")
        return 1

    stdout.write(json.dumps({"decision": "allow"}) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main_hook_entrypoint())

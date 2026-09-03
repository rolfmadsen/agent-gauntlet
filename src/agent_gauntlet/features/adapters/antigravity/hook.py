"""CLI PreInvocation Hook entrypoint for Google Antigravity IDE."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import TextIO

from agent_gauntlet.features.adapters.antigravity.adapter import AntigravityAdapter
from agent_gauntlet.features.adapters.antigravity.shim import AntigravityHookShim
from agent_gauntlet.features.supervisor.platform.linux.ipc import UnixDomainSocketTransport


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

    # 1. Attempt evaluation via supervisor over IPC if socket exists or configured
    socket_override = os.environ.get("AGENT_GAUNTLET_SUPERVISOR_SOCKET")
    strict_supervisor = os.environ.get("AGENT_GAUNTLET_STRICT_SUPERVISOR") == "1"
    transport = UnixDomainSocketTransport(Path(socket_override) if socket_override else None)
    if transport.socket_path.exists():
        shim = AntigravityHookShim(transport=transport)
        workspace_id = str(active_workspace)
        hook_res = shim.handle_hook(payload=payload, workspace_id=workspace_id)
        if hook_res.get("offline", False) and not strict_supervisor and not socket_override:
            # Stale socket detected while in unsupervised local mode: fall back to in-process adapter
            pass
        else:
            if hook_res.get("decision") != "allow":
                reason = str(hook_res.get("reason", "Denied by supervisor daemon."))
                output_payload = {"decision": "deny", "reason": reason}
                stdout.write(json.dumps(output_payload) + "\n")
                stderr.write(f"\n{reason}\n")
                return 1
            stdout.write(json.dumps({"decision": "allow"}) + "\n")
            return 0

    # 2. Fallback to in-process AntigravityAdapter evaluation
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

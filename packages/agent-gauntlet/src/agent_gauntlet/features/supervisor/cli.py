"""CLI command handlers for supervisor daemon management."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from agent_gauntlet.features.supervisor.core.engine import SupervisorEngine
from agent_gauntlet.features.supervisor.core.models import RpcMethod, RpcRequest
from agent_gauntlet.features.supervisor.platform.linux.ipc import UnixDomainSocketTransport
from agent_gauntlet.features.supervisor.platform.linux.server import SupervisorServer


def execute_supervisor_cli(args: argparse.Namespace, workspace: Path) -> int:
    """Dispatches supervisor daemon start and status subcommands."""
    raw_socket = getattr(args, "socket_path", "")
    socket_path = Path(raw_socket).resolve() if raw_socket else None

    if args.supervisor_subcommand == "start":
        if getattr(args, "daemon", False):
            import subprocess
            import sys
            import time

            target_socket = socket_path or SupervisorServer(socket_path=socket_path).socket_path
            task_id = getattr(args, "task_id", "")

            cmd = [
                sys.executable,
                "-m",
                "agent_gauntlet.cli",
                "-w",
                str(workspace),
                "supervisor",
                "start",
                "--socket-path",
                str(target_socket),
            ]
            if task_id:
                cmd.extend(["--task-id", task_id])

            env = os.environ.copy()
            repo_root = Path(__file__).resolve().parent.parent.parent.parent
            src_dir = repo_root / "src"
            if src_dir.exists():
                existing = env.get("PYTHONPATH", "")
                env["PYTHONPATH"] = f"{src_dir}:{existing}" if existing else str(src_dir)

            proc = subprocess.Popen(
                cmd,
                env=env,
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )

            deadline = time.time() + 3.0
            ready = False
            transport = UnixDomainSocketTransport(socket_path=target_socket)
            probe_req = RpcRequest(id="daemon_probe", method=RpcMethod.GET_STATUS)

            while time.time() < deadline:
                if proc.poll() is not None:
                    break
                if target_socket.exists():
                    try:
                        probe_res = transport.send_rpc(probe_req, timeout_seconds=0.2)
                        if probe_res.is_success:
                            ready = True
                            break
                    except Exception:
                        pass
                time.sleep(0.05)

            if not ready:
                if args.json:
                    print(
                        json.dumps(
                            {
                                "status": "FAILED",
                                "error": "Supervisor daemon failed to start within timeout",
                                "exit_code": proc.poll(),
                            },
                            indent=2,
                        )
                    )
                else:
                    print("[-] Failed to start supervisor daemon in background.")
                return 1

            proc.returncode = 0  # Intentionally detached daemon process

            if args.json:
                print(
                    json.dumps(
                        {
                            "status": "STARTED",
                            "socket": str(target_socket),
                            "workspace": str(workspace),
                            "pid": proc.pid,
                        },
                        indent=2,
                    )
                )
            else:
                print(
                    f"[+] Supervisor daemon started in background on {target_socket} (PID: {proc.pid})"
                )
            return 0

        # Foreground mode
        engine = SupervisorEngine()
        server = SupervisorServer(engine=engine, socket_path=socket_path)
        engine.register_workspace(str(workspace), str(workspace))
        task_id = getattr(args, "task_id", "")
        if task_id:
            engine.begin_or_resume_session(str(workspace), task_id)
        if args.json:
            print(
                json.dumps(
                    {
                        "status": "RUNNING",
                        "socket": str(server.socket_path),
                        "workspace": str(workspace),
                    },
                    indent=2,
                )
            )
        else:
            print(f"[+] Starting supervisor daemon on {server.socket_path} (Ctrl+C to stop)...")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.stop()
            print("\n[-] Supervisor daemon stopped.")
        return 0

    if args.supervisor_subcommand == "status":
        transport = UnixDomainSocketTransport(socket_path=socket_path)
        req = RpcRequest(id="cli_status", method=RpcMethod.GET_STATUS)
        try:
            res = transport.send_rpc(req, timeout_seconds=2.0)
            if not res.is_success or not res.result:
                if args.json:
                    print(json.dumps({"running": False, "error": res.error}, indent=2))
                else:
                    print(f"[-] Supervisor returned error: {res.error}")
                return 1

            if args.json:
                print(json.dumps({"running": True, "details": res.result}, indent=2))
            else:
                st = res.result.get("status", "UNKNOWN")
                print(f"[+] Supervisor status: {st} (endpoint: {transport.get_socket_endpoint()})")
            return 0
        except Exception as exc:
            if args.json:
                print(json.dumps({"running": False, "error": str(exc)}, indent=2))
            else:
                print(f"[-] Supervisor daemon is offline or unreachable: {exc}")
            return 1

    return 2

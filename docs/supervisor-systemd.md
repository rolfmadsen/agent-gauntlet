---
type: Documentation
status: stable
title: "Agent-Gauntlet Supervisor Systemd Socket Activation Guide"
verified_by: "process:agent-gauntlet"
verified_at: "2026-09-03T16:28:11Z"
generated_by: "antigravity/gemini-3.8-flash"
generated_at: "2026-09-03T16:28:11Z"
---

# Agent-Gauntlet Supervisor Systemd Socket Activation Guide

This guide documents the architecture, installation, and operational maintenance of the **Agent-Gauntlet Supervisor Daemon** under Linux with native **systemd socket activation**.

---

## 🛡️ Architectural Overview

The **Supervisor Daemon** is an OS-level privileged watchdog responsible for enforcing fail-closed security invariants, managing isolated task sessions, and hosting the dual-mode policy evaluation engine (`gauntlet-policy-engine`).

```text
┌─────────────────────────────────────────────────────────────┐
│                    Developer Machine (OS)                   │
│                                                             │
│   ┌─────────────────────┐         Unix Domain Socket        │
│   │   Antigravity IDE   │ ──────────────────────────────┐   │
│   │ (PreInvocation Hook)│                               │   │
│   └─────────────────────┘                               ▼   │
│                                                 ┌─────────┐ │
│                                                 │ systemd │ │
│   ┌─────────────────────┐                       │ .socket │ │
│   │     Claude Code     │ ──────────────────────┤ (FD 3)  │ │
│   │    (PreToolUse)     │                       └────┬────┘ │
│   └─────────────────────┘                            │      │
│                                           Activation │      │
│                                                      ▼      │
│                                   ┌───────────────────────┐ │
│                                   │ agent-gauntlet daemon │ │
│                                   │  - SupervisorEngine   │ │
│                                   │  - LinuxKeyProvider   │ │
│                                   │  - WasmPolicyVerifier │ │
│                                   └───────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Security Guarantees
1. **Fail-Closed Gatekeeper**: If the supervisor is offline or communication fails, all state-modifying operations (`write_to_file`, `replace_file_content`, `run_command` with mutating commands) are strictly blocked.
2. **Task Session Binding**: Modifying operations require an active, ongoing task session (`ACTIVE` status in `tasks/<number>-*.md`).
3. **Zero Boot Latency via Socket Activation**: systemd binds and listens on `/run/user/<UID>/agent-gauntlet/supervisor.sock` on boot. The daemon process only starts when the first tool call is invoked by the IDE.

---

## 📦 Systemd Unit Configuration

Configure user-level systemd units so the supervisor daemon runs unprivileged within the developer user session.

### 1. Socket Unit: `~/.config/systemd/user/agent-gauntlet-supervisor.socket`

```ini
[Unit]
Description=Agent Gauntlet Supervisor Socket
PartOf=agent-gauntlet-supervisor.service

[Socket]
ListenStream=%t/agent-gauntlet/supervisor.sock
SocketMode=0600
DirectoryMode=0700

[Install]
WantedBy=sockets.target
```

*Note: `%t` resolves to the systemd runtime directory for the user, typically `/run/user/<UID>`.*

---

### 2. Service Unit: `~/.config/systemd/user/agent-gauntlet-supervisor.service`

```ini
[Unit]
Description=Agent Gauntlet Supervisor Daemon
Requires=agent-gauntlet-supervisor.socket
After=agent-gauntlet-supervisor.socket

[Service]
Type=simple
ExecStart=/usr/local/bin/agent-gauntlet supervisor start
StandardInput=socket
Restart=on-failure
RestartSec=2s

# Sandboxing and Security hardening
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=%t/agent-gauntlet %h/.local/share/agent-gauntlet
NoNewPrivileges=true

[Install]
WantedBy=default.target
```

---

## 🚀 Installation & Activation Steps

1. **Create the unit directory**:
   ```bash
   mkdir -p ~/.config/systemd/user
   ```

2. **Install unit files**:
   Copy the socket and service unit configurations above into:
   - `~/.config/systemd/user/agent-gauntlet-supervisor.socket`
   - `~/.config/systemd/user/agent-gauntlet-supervisor.service`

3. **Reload systemd user daemon**:
   ```bash
   systemctl --user daemon-reload
   ```

4. **Enable and start the socket**:
   ```bash
   systemctl --user enable --now agent-gauntlet-supervisor.socket
   ```

5. **Verify socket status**:
   ```bash
   systemctl --user status agent-gauntlet-supervisor.socket
   ```

---

## 🔍 Verification & Health Inspection

Check daemon connectivity using the built-in CLI commands:

### Check Status
```bash
agent-gauntlet supervisor status
```
Output:
```text
[+] Supervisor status: HEALTHY (endpoint: /run/user/1000/agent-gauntlet/supervisor.sock)
```

### JSON Output
```bash
agent-gauntlet supervisor status --json
```
Output:
```json
{
  "running": true,
  "details": {
    "status": "HEALTHY",
    "engine": "active",
    "active_sessions": 1,
    "registered_workspaces": 1
  }
}
```

---

## 🔧 Environment Variables Reference

| Variable | Description | Default |
|---|---|---|
| `AGENT_GAUNTLET_SUPERVISOR_SOCKET` | Explicit socket path override | `$XDG_RUNTIME_DIR/agent-gauntlet/supervisor.sock` |
| `AGENT_GAUNTLET_KEY_DIR` | Directory for cryptographic keys | `$XDG_DATA_HOME/agent-gauntlet/keys` |
| `AGENT_GAUNTLET_POLICY_NATIVE` | Absolute path to `libpolicy_engine.so` | Auto-detected |
| `AGENT_GAUNTLET_POLICY_WASM` | Absolute path to `policy_engine.wasm` | Auto-detected |

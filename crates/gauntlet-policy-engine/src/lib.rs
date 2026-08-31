//! Deterministic zero-authority WebAssembly policy engine for Agent Gauntlet.
//!
//! Evaluates strongly-typed capability requests against an immutable trusted context.

pub const POLICY_VERSION: &str = "0.7.0";


#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ToolActionType {
    ReadFile,
    WriteFile,
    ExecuteCommand,
    Other,
}

impl ToolActionType {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::ReadFile => "read_file",
            Self::WriteFile => "write_file",
            Self::ExecuteCommand => "execute_command",
            Self::Other => "other",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CapabilityRequest {
    pub action_type: ToolActionType,
    pub raw_tool_name: String,
    pub target_resource: String,
    pub payload_json: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EnforcementContext {
    pub workspace_id: String,
    pub has_active_task: bool,
    pub active_task_id: String,
    pub read_only: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DecisionVerdict {
    Allow,
    Deny,
    Ask,
    ForceAsk,
}

impl DecisionVerdict {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Allow => "allow",
            Self::Deny => "deny",
            Self::Ask => "ask",
            Self::ForceAsk => "force_ask",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PolicyDecision {
    pub verdict: DecisionVerdict,
    pub reason: String,
    pub reason_code: u32,
}

/// Deterministically evaluates a capability request against trusted context.
pub fn evaluate(req: &CapabilityRequest, ctx: &EnforcementContext) -> PolicyDecision {
    if ctx.read_only {
        if matches!(req.action_type, ToolActionType::WriteFile | ToolActionType::ExecuteCommand) {
            return PolicyDecision {
                verdict: DecisionVerdict::Deny,
                reason: "Workspace is in read-only mode; state mutation is prohibited.".into(),
                reason_code: 4030,
            };
        }
    }

    match req.action_type {
        ToolActionType::ReadFile => PolicyDecision {
            verdict: DecisionVerdict::Allow,
            reason: "Read operations are unrestricted.".into(),
            reason_code: 2000,
        },
        ToolActionType::WriteFile => {
            let target = req.target_resource.replace('\\', "/");
            let target_str = target.trim();

            if target_str.starts_with("tasks/")
                || target_str == "spec.md"
                || target_str == "CONTEXT.md"
                || target_str == "CODING_STANDARDS.md"
                || target_str == "README.md"
                || target_str.starts_with("docs/")
            {
                return PolicyDecision {
                    verdict: DecisionVerdict::Allow,
                    reason: "Writing task definitions or domain documentation is permitted.".into(),
                    reason_code: 2001,
                };
            }

            if target_str.starts_with("src/")
                || target_str.starts_with("tests/")
                || target_str.starts_with("packages/")
            {
                if !ctx.has_active_task {
                    return PolicyDecision {
                        verdict: DecisionVerdict::Deny,
                        reason: "Writing to production code without active task is prohibited.".into(),
                        reason_code: 4031,
                    };
                }
                return PolicyDecision {
                    verdict: DecisionVerdict::Allow,
                    reason: format!("Writing to code permitted under active task '{}'.", ctx.active_task_id),
                    reason_code: 2002,
                };
            }

            if !ctx.has_active_task {
                PolicyDecision {
                    verdict: DecisionVerdict::Deny,
                    reason: "Mutating repository files without an active task is prohibited.".into(),
                    reason_code: 4032,
                }
            } else {
                PolicyDecision {
                    verdict: DecisionVerdict::Allow,
                    reason: "Write operation permitted under active task.".into(),
                    reason_code: 2003,
                }
            }
        }
        ToolActionType::ExecuteCommand => {
            let cmd = req.target_resource.trim();
            let safe_prefixes = [
                "git status",
                "git diff",
                "git log",
                "ls",
                "pwd",
                "echo",
                "which",
                "pytest",
                "python -m unittest",
                "python3 -m unittest",
                "cargo check",
                "cargo test",
                "ruff check",
                "pyright",
                "agent-gauntlet verify",
                "sh tools/gauntlet.sh",
            ];
            if safe_prefixes.iter().any(|prefix| cmd.starts_with(prefix)) {
                return PolicyDecision {
                    verdict: DecisionVerdict::Allow,
                    reason: "Read-only or verification command is permitted.".into(),
                    reason_code: 2004,
                };
            }

            if !ctx.has_active_task {
                PolicyDecision {
                    verdict: DecisionVerdict::Deny,
                    reason: "Executing modifying commands without an active task is prohibited.".into(),
                    reason_code: 4033,
                }
            } else {
                PolicyDecision {
                    verdict: DecisionVerdict::Allow,
                    reason: "Command execution permitted under active task.".into(),
                    reason_code: 2005,
                }
            }
        }
        ToolActionType::Other => PolicyDecision {
            verdict: DecisionVerdict::Allow,
            reason: "Other capability request permitted by default.".into(),
            reason_code: 2000,
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_read_is_unrestricted() {
        let req = CapabilityRequest {
            action_type: ToolActionType::ReadFile,
            raw_tool_name: "view_file".into(),
            target_resource: "src/main.rs".into(),
            payload_json: "{}".into(),
        };
        let ctx = EnforcementContext {
            workspace_id: "ws-1".into(),
            has_active_task: false,
            active_task_id: "".into(),
            read_only: false,
        };
        let dec = evaluate(&req, &ctx);
        assert_eq!(dec.verdict, DecisionVerdict::Allow);
    }

    #[test]
    fn test_write_without_task_denied() {
        let req = CapabilityRequest {
            action_type: ToolActionType::WriteFile,
            raw_tool_name: "write_to_file".into(),
            target_resource: "src/lib.rs".into(),
            payload_json: "{}".into(),
        };
        let ctx = EnforcementContext {
            workspace_id: "ws-1".into(),
            has_active_task: false,
            active_task_id: "".into(),
            read_only: false,
        };
        let dec = evaluate(&req, &ctx);
        assert_eq!(dec.verdict, DecisionVerdict::Deny);
        assert_eq!(dec.reason_code, 4031);
    }

    #[test]
    fn test_write_with_task_allowed() {
        let req = CapabilityRequest {
            action_type: ToolActionType::WriteFile,
            raw_tool_name: "write_to_file".into(),
            target_resource: "src/lib.rs".into(),
            payload_json: "{}".into(),
        };
        let ctx = EnforcementContext {
            workspace_id: "ws-1".into(),
            has_active_task: true,
            active_task_id: "035-test".into(),
            read_only: false,
        };
        let dec = evaluate(&req, &ctx);
        assert_eq!(dec.verdict, DecisionVerdict::Allow);
    }
}

//! Deterministic zero-authority WebAssembly policy engine for Agent Gauntlet.
//!
//! Evaluates strongly-typed capability requests against an immutable trusted context.

pub const POLICY_VERSION: &str = "0.8.1";


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

fn escape_json(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 16);
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            other => out.push(other),
        }
    }
    out
}

fn find_top_level_key_value<'a>(json: &'a str, target_key: &str) -> Option<&'a str> {
    let bytes = json.as_bytes();
    let mut i = 0;
    let len = bytes.len();
    let mut depth: usize = 0;
    let mut in_str = false;
    let mut escaped = false;

    // Find the opening brace of the root object
    while i < len {
        let b = bytes[i];
        if !in_str && b == b'{' {
            depth = 1;
            i += 1;
            break;
        }
        i += 1;
    }

    while i < len {
        let b = bytes[i];
        if escaped {
            escaped = false;
            i += 1;
            continue;
        }
        if b == b'\\' && in_str {
            escaped = true;
            i += 1;
            continue;
        }
        if b == b'"' {
            in_str = !in_str;
            if in_str && depth == 1 {
                // Potential key start at depth 1
                let key_start = i + 1;
                i += 1;
                while i < len {
                    if escaped {
                        escaped = false;
                    } else if bytes[i] == b'\\' {
                        escaped = true;
                    } else if bytes[i] == b'"' {
                        let key = &json[key_start..i];
                        in_str = false;
                        i += 1;
                        // Skip whitespace to colon
                        while i < len
                            && (bytes[i] == b' '
                                || bytes[i] == b'\t'
                                || bytes[i] == b'\n'
                                || bytes[i] == b'\r')
                        {
                            i += 1;
                        }
                        if i < len && bytes[i] == b':' {
                            i += 1;
                            // Skip whitespace after colon
                            while i < len
                                && (bytes[i] == b' '
                                    || bytes[i] == b'\t'
                                    || bytes[i] == b'\n'
                                    || bytes[i] == b'\r')
                            {
                                i += 1;
                            }
                            if key == target_key {
                                let val_start = i;
                                if i < len && bytes[i] == b'"' {
                                    // String value
                                    i += 1;
                                    let mut s_escaped = false;
                                    while i < len {
                                        if s_escaped {
                                            s_escaped = false;
                                        } else if bytes[i] == b'\\' {
                                            s_escaped = true;
                                        } else if bytes[i] == b'"' {
                                            i += 1;
                                            return Some(&json[val_start..i]);
                                        }
                                        i += 1;
                                    }
                                    return Some(&json[val_start..i]);
                                } else if i < len && (bytes[i] == b'{' || bytes[i] == b'[') {
                                    let mut val_depth = 1;
                                    let open_b = bytes[i];
                                    let close_b = if open_b == b'{' { b'}' } else { b']' };
                                    let mut v_in_str = false;
                                    let mut v_escaped = false;
                                    i += 1;
                                    while i < len {
                                        let vb = bytes[i];
                                        if v_escaped {
                                            v_escaped = false;
                                        } else if vb == b'\\' && v_in_str {
                                            v_escaped = true;
                                        } else if vb == b'"' {
                                            v_in_str = !v_in_str;
                                        } else if !v_in_str {
                                            if vb == open_b {
                                                val_depth += 1;
                                            } else if vb == close_b {
                                                val_depth -= 1;
                                                if val_depth == 0 {
                                                    i += 1;
                                                    return Some(&json[val_start..i]);
                                                }
                                            }
                                        }
                                        i += 1;
                                    }
                                    return Some(&json[val_start..i]);
                                } else {
                                    // Primitive value
                                    while i < len
                                        && bytes[i] != b','
                                        && bytes[i] != b'}'
                                        && bytes[i] != b' '
                                        && bytes[i] != b'\t'
                                        && bytes[i] != b'\n'
                                        && bytes[i] != b'\r'
                                    {
                                        i += 1;
                                    }
                                    return Some(&json[val_start..i]);
                                }
                            }
                        }
                        break;
                    }
                    i += 1;
                }
                continue;
            }
            i += 1;
            continue;
        }

        if !in_str {
            if b == b'{' || b == b'[' {
                depth += 1;
            } else if b == b'}' || b == b']' {
                if depth > 0 {
                    depth -= 1;
                }
                if depth == 0 {
                    break;
                }
            }
        }
        i += 1;
    }
    None
}

fn unescape_json_str(s: &str) -> String {
    if !s.starts_with('"') || !s.ends_with('"') || s.len() < 2 {
        return s.to_string();
    }
    let inner = &s[1..s.len() - 1];
    let mut out = String::with_capacity(inner.len());
    let mut chars = inner.chars();
    let mut escaped = false;
    while let Some(c) = chars.next() {
        if escaped {
            match c {
                'n' => out.push('\n'),
                'r' => out.push('\r'),
                't' => out.push('\t'),
                '\\' => out.push('\\'),
                '"' => out.push('"'),
                _ => {
                    out.push('\\');
                    out.push(c);
                }
            }
            escaped = false;
        } else if c == '\\' {
            escaped = true;
        } else {
            out.push(c);
        }
    }
    out
}

fn extract_json_str(json: &str, key: &str) -> Option<String> {
    let raw = find_top_level_key_value(json, key)?;
    if raw.starts_with('"') {
        Some(unescape_json_str(raw))
    } else if raw.starts_with('{') || raw.starts_with('[') {
        Some(raw.to_string())
    } else {
        Some(raw.trim().to_string())
    }
}

fn extract_json_bool(json: &str, key: &str) -> Option<bool> {
    let raw = find_top_level_key_value(json, key)?;
    let trimmed = raw.trim();
    if trimmed.starts_with("true") {
        Some(true)
    } else if trimmed.starts_with("false") {
        Some(false)
    } else {
        None
    }
}

pub fn parse_capability_request(json: &str) -> CapabilityRequest {
    let action_str = extract_json_str(json, "action_type").unwrap_or_default();
    let action_type = match action_str.as_str() {
        "read_file" => ToolActionType::ReadFile,
        "write_file" => ToolActionType::WriteFile,
        "execute_command" => ToolActionType::ExecuteCommand,
        _ => ToolActionType::Other,
    };
    let raw_tool_name = extract_json_str(json, "raw_tool_name").unwrap_or_default();
    let target_resource = extract_json_str(json, "target_resource").unwrap_or_default();
    let payload_json = extract_json_str(json, "payload_json").unwrap_or_default();

    CapabilityRequest {
        action_type,
        raw_tool_name,
        target_resource,
        payload_json,
    }
}

pub fn parse_enforcement_context(json: &str) -> EnforcementContext {
    let workspace_id = extract_json_str(json, "workspace_id").unwrap_or_default();
    let has_active_task = extract_json_bool(json, "has_active_task").unwrap_or(false);
    let active_task_id = extract_json_str(json, "active_task_id").unwrap_or_default();
    let read_only = extract_json_bool(json, "read_only").unwrap_or(false);

    EnforcementContext {
        workspace_id,
        has_active_task,
        active_task_id,
        read_only,
    }
}

impl PolicyDecision {
    pub fn to_json(&self) -> String {
        format!(
            r#"{{"verdict":"{}","reason":"{}","reason_code":{}}}"#,
            self.verdict.as_str(),
            escape_json(&self.reason),
            self.reason_code
        )
    }
}

#[no_mangle]
pub extern "C" fn alloc(size: usize) -> *mut u8 {
    let mut buf = Vec::with_capacity(size);
    let ptr = buf.as_mut_ptr();
    std::mem::forget(buf);
    ptr
}

#[no_mangle]
pub unsafe extern "C" fn dealloc(ptr: *mut u8, size: usize) {
    if !ptr.is_null() && size > 0 {
        let _ = Vec::from_raw_parts(ptr, 0, size);
    }
}

#[no_mangle]
pub unsafe extern "C" fn evaluate_json(
    req_ptr: *const u8,
    req_len: usize,
    ctx_ptr: *const u8,
    ctx_len: usize,
    out_len: *mut usize,
) -> *mut u8 {
    let req_bytes = std::slice::from_raw_parts(req_ptr, req_len);
    let ctx_bytes = std::slice::from_raw_parts(ctx_ptr, ctx_len);
    let req_str = std::str::from_utf8(req_bytes).unwrap_or("");
    let ctx_str = std::str::from_utf8(ctx_bytes).unwrap_or("");

    let req = parse_capability_request(req_str);
    let ctx = parse_enforcement_context(ctx_str);
    let decision = evaluate(&req, &ctx);
    let mut json_out = decision.to_json().into_bytes();
    json_out.shrink_to_fit();

    if !out_len.is_null() {
        *out_len = json_out.len();
    }
    let ptr = json_out.as_mut_ptr();
    std::mem::forget(json_out);
    ptr
}

#[no_mangle]
pub unsafe extern "C" fn evaluate_json_wasm(
    req_ptr: u32,
    req_len: u32,
    ctx_ptr: u32,
    ctx_len: u32,
) -> u64 {
    let mut out_len: usize = 0;
    let ptr = evaluate_json(
        req_ptr as *const u8,
        req_len as usize,
        ctx_ptr as *const u8,
        ctx_len as usize,
        &mut out_len,
    );
    ((out_len as u64) << 32) | ((ptr as usize as u64) & 0xFFFFFFFF)
}

#[no_mangle]
pub extern "C" fn get_policy_version_ptr() -> *const u8 {
    POLICY_VERSION.as_ptr()
}

#[no_mangle]
pub extern "C" fn get_policy_version_len() -> usize {
    POLICY_VERSION.len()
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

    #[test]
    fn test_json_roundtrip_evaluation() {
        let req_json = r#"{"action_type":"write_file","raw_tool_name":"write_to_file","target_resource":"src/lib.rs","payload_json":"{}"}"#;
        let ctx_json = r#"{"workspace_id":"ws-1","has_active_task":false,"active_task_id":"","read_only":false}"#;

        unsafe {
            let mut out_len: usize = 0;
            let ptr = evaluate_json(
                req_json.as_ptr(),
                req_json.len(),
                ctx_json.as_ptr(),
                ctx_json.len(),
                &mut out_len,
            );
            assert!(!ptr.is_null());
            assert!(out_len > 0);
            let res_bytes = std::slice::from_raw_parts(ptr, out_len);
            let res_str = std::str::from_utf8(res_bytes).unwrap();
            assert!(res_str.contains(r#""verdict":"deny""#));
            assert!(res_str.contains(r#""reason_code":4031"#));
            dealloc(ptr, out_len);
        }
    }

    #[test]
    fn test_json_nested_payload_does_not_spoof_action_type() {
        // payload_json comes FIRST and contains a deceptive "action_type":"read_file" inside a nested string
        let req_json = r#"{"payload_json":"{\"action_type\":\"read_file\",\"raw_tool_name\":\"fake\"}","raw_tool_name":"write_to_file","target_resource":"src/lib.rs","action_type":"write_file"}"#;
        let req = parse_capability_request(req_json);
        assert_eq!(req.action_type, ToolActionType::WriteFile);
        assert_eq!(req.raw_tool_name, "write_to_file");
        assert_eq!(req.target_resource, "src/lib.rs");

        let ctx_json = r#"{"workspace_id":"ws-1","has_active_task":false,"read_only":false}"#;
        let ctx = parse_enforcement_context(ctx_json);
        assert_eq!(ctx.has_active_task, false);

        let dec = evaluate(&req, &ctx);
        assert_eq!(dec.verdict, DecisionVerdict::Deny);
        assert_eq!(dec.reason_code, 4031);
    }
}

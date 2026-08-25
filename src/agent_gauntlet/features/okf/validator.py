"""Strict validator for Open Knowledge Format (OKF v0.2) compliance."""

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from agent_gauntlet.features.okf.models import (
    Actor,
    OkfValidationFinding,
    OkfValidationReport,
    StatusEnum,
)

# ISO 8601 regex ensuring time component exists and UTC / explicit offset is present
ISO8601_REGEX = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})$"
)


def parse_frontmatter(content: str) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """Extract YAML frontmatter and markdown body from file content.

    Returns:
        (metadata_dict, body_content, error_message)
    """
    if not content.startswith("---"):
        return None, content, None

    # Split on closing delimiter
    lines = content.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, content, None

    closing_index = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            closing_index = i
            break

    if closing_index == -1:
        return None, content, "Unclosed YAML frontmatter block (missing terminating '---')"

    yaml_text = "".join(lines[1:closing_index])
    body = "".join(lines[closing_index + 1 :])

    try:
        data = yaml.safe_load(yaml_text)
        if data is None:
            data = {}
        elif not isinstance(data, dict):
            return None, body, f"Frontmatter must parse to a mapping/dictionary, got: {type(data).__name__}"
        return data, body, None
    except Exception as exc:
        return None, body, f"Invalid YAML frontmatter: {exc}"


def validate_iso_timestamp(timestamp_val: Any) -> Tuple[Optional[datetime], Optional[str]]:
    """Validate and parse an ISO 8601 UTC timestamp."""
    if isinstance(timestamp_val, datetime):
        if timestamp_val.tzinfo is None:
            return None, "Timestamp must include timezone offset (e.g. 'Z' or '+00:00')"
        return timestamp_val.astimezone(timezone.utc), None

    if not isinstance(timestamp_val, str):
        return None, f"Timestamp must be a string or datetime, got {type(timestamp_val).__name__}"

    val_str = timestamp_val.strip()
    if not ISO8601_REGEX.match(val_str):
        return None, f"Timestamp {val_str!r} does not match strict ISO 8601 UTC format (YYYY-MM-DDTHH:MM:SSZ)"

    try:
        # Standardize Z to +00:00 for fromisoformat
        iso_clean = val_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso_clean)
        if dt.tzinfo is None:
            return None, "Timestamp must include explicit timezone offset"
        return dt.astimezone(timezone.utc), None
    except Exception as exc:
        return None, f"Invalid ISO 8601 timestamp {val_str!r}: {exc}"


def validate_actor(actor_val: Any) -> Tuple[Optional[Actor], Optional[str]]:
    """Validate and parse an actor identity."""
    try:
        actor = Actor.parse(str(actor_val))
        return actor, None
    except Exception as exc:
        return None, str(exc)


def validate_okf_metadata(
    meta: Dict[str, Any],
    file_path: str = "",
    now: Optional[datetime] = None,
) -> List[OkfValidationFinding]:
    """Validate parsed frontmatter dictionary against OKF v0.2 rules."""
    findings: List[OkfValidationFinding] = []
    current_time = now or datetime.now(timezone.utc)
    future_tolerance = current_time + timedelta(seconds=60)

    # 1. Required 'type' field
    doc_type = meta.get("type")
    if not doc_type or not str(doc_type).strip():
        findings.append(
            OkfValidationFinding(
                file_path=file_path,
                rule="REQUIRED_TYPE",
                message="Missing or empty required frontmatter field: 'type'.",
                remediation_hint="Add 'type: <Concept Type>' (e.g. 'Task Package', 'Architectural Decision Record', 'System Specification') to frontmatter.",
            )
        )

    # 2. Status field validation
    status = meta.get("status")
    if status is not None:
        valid_statuses = {s.value for s in StatusEnum}
        if status not in valid_statuses:
            findings.append(
                OkfValidationFinding(
                    file_path=file_path,
                    rule="INVALID_STATUS",
                    message=f"Invalid status value {status!r}. Must be one of: {sorted(valid_statuses)}.",
                    remediation_hint="Set 'status: draft', 'status: stable', or 'status: deprecated'.",
                )
            )

    # 3. Generated block validation
    generated_dt: Optional[datetime] = None
    generated = meta.get("generated")
    if generated is not None:
        if not isinstance(generated, dict):
            findings.append(
                OkfValidationFinding(
                    file_path=file_path,
                    rule="INVALID_GENERATED_BLOCK",
                    message="Field 'generated' must be a dictionary with 'by' and optional 'at'.",
                    remediation_hint="Format as 'generated: { by: <actor>, at: <ISO-timestamp> }'.",
                )
            )
        else:
            by_val = generated.get("by")
            _, actor_err = validate_actor(by_val)
            if actor_err:
                findings.append(
                    OkfValidationFinding(
                        file_path=file_path,
                        rule="INVALID_ACTOR",
                        message=f"Invalid 'generated.by' actor: {actor_err}",
                        remediation_hint="Use 'human:<id>', '<agent>/<version>', or 'process:<id>'.",
                    )
                )

            at_val = generated.get("at")
            if at_val is not None:
                dt, dt_err = validate_iso_timestamp(at_val)
                if dt_err:
                    findings.append(
                        OkfValidationFinding(
                            file_path=file_path,
                            rule="INVALID_TIMESTAMP",
                            message=f"Invalid 'generated.at' timestamp: {dt_err}",
                            remediation_hint="Provide ISO 8601 UTC timestamp like '2026-08-23T15:00:00Z'.",
                        )
                    )
                else:
                    generated_dt = dt
                    if dt is not None and dt > future_tolerance:
                        findings.append(
                            OkfValidationFinding(
                                file_path=file_path,
                                rule="FUTURE_TIMESTAMP",
                                message=f"'generated.at' ({at_val}) is in the future beyond clock skew tolerance.",
                                remediation_hint="Use current UTC time for timestamp.",
                            )
                        )

    # 4. Verified list validation
    verified = meta.get("verified")
    if verified is not None:
        verified_list: List[Any] = verified if isinstance(verified, list) else [verified]
        for idx, entry in enumerate(verified_list):
            if not isinstance(entry, dict):
                findings.append(
                    OkfValidationFinding(
                        file_path=file_path,
                        rule="INVALID_VERIFIED_ENTRY",
                        message=f"'verified' entry #{idx+1} must be a dictionary with 'by' and 'at'.",
                        remediation_hint="Format as '{ by: <actor>, at: <ISO-timestamp> }'.",
                    )
                )
                continue

            by_val = entry.get("by")
            _, actor_err = validate_actor(by_val)
            if actor_err:
                findings.append(
                    OkfValidationFinding(
                        file_path=file_path,
                        rule="INVALID_ACTOR",
                        message=f"Invalid 'verified[{idx}].by' actor: {actor_err}",
                        remediation_hint="Use 'human:<id>', '<agent>/<version>', or 'process:<id>'.",
                    )
                )

            at_val = entry.get("at")
            if at_val is None:
                findings.append(
                    OkfValidationFinding(
                        file_path=file_path,
                        rule="MISSING_VERIFIED_TIMESTAMP",
                        message=f"'verified[{idx}]' is missing required 'at' timestamp.",
                        remediation_hint="Add 'at: <ISO-timestamp>' to the verified entry.",
                    )
                )
            else:
                dt, dt_err = validate_iso_timestamp(at_val)
                if dt_err:
                    findings.append(
                        OkfValidationFinding(
                            file_path=file_path,
                            rule="INVALID_TIMESTAMP",
                            message=f"Invalid 'verified[{idx}].at' timestamp: {dt_err}",
                            remediation_hint="Provide ISO 8601 UTC timestamp like '2026-08-23T15:00:00Z'.",
                        )
                    )
                else:
                    if dt is not None and dt > future_tolerance:
                        findings.append(
                            OkfValidationFinding(
                                file_path=file_path,
                                rule="FUTURE_TIMESTAMP",
                                message=f"'verified[{idx}].at' ({at_val}) is in the future beyond tolerance.",
                                remediation_hint="Use current UTC time for verification timestamp.",
                            )
                        )
                    if generated_dt is not None and dt is not None and dt < generated_dt:
                        gen_at_val = generated.get("at") if isinstance(generated, dict) else ""
                        findings.append(
                            OkfValidationFinding(
                                file_path=file_path,
                                rule="CHRONOLOGICAL_INVERSION",
                                message=f"'verified[{idx}].at' ({at_val}) precedes 'generated.at' ({gen_at_val}).",
                                remediation_hint="Verification cannot occur prior to document generation.",
                            )
                        )

    # 5. Stale_after validation
    stale_after = meta.get("stale_after")
    if stale_after is not None:
        _, dt_err = validate_iso_timestamp(stale_after)
        if dt_err:
            findings.append(
                OkfValidationFinding(
                    file_path=file_path,
                    rule="INVALID_TIMESTAMP",
                    message=f"Invalid 'stale_after' timestamp: {dt_err}",
                    remediation_hint="Provide ISO 8601 UTC timestamp like '2026-12-31T23:59:59Z'.",
                )
            )

    # 6. Sources list validation
    sources = meta.get("sources")
    if sources is not None:
        if not isinstance(sources, list):
            findings.append(
                OkfValidationFinding(
                    file_path=file_path,
                    rule="INVALID_SOURCES_FORMAT",
                    message="'sources' must be a list of source entries.",
                    remediation_hint="Format as a list: 'sources: [ { id: ..., resource: ... } ]'.",
                )
            )
        else:
            for idx, src in enumerate(sources):
                if not isinstance(src, dict):
                    findings.append(
                        OkfValidationFinding(
                            file_path=file_path,
                            rule="INVALID_SOURCE_ENTRY",
                            message=f"'sources[{idx}]' must be a dictionary.",
                            remediation_hint="Provide a mapping with at least 'resource'.",
                        )
                    )
                elif not src.get("resource") or not str(src.get("resource")).strip():
                    findings.append(
                        OkfValidationFinding(
                            file_path=file_path,
                            rule="SOURCE_MISSING_RESOURCE",
                            message=f"'sources[{idx}]' is missing required 'resource' field.",
                            remediation_hint="Provide a path or URI in 'resource'.",
                        )
                    )

    return findings


def validate_okf_file(
    file_path: Path,
    now: Optional[datetime] = None,
) -> List[OkfValidationFinding]:
    """Validate a single Markdown file for OKF compliance."""
    rel_path = str(file_path)
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as exc:
        return [
            OkfValidationFinding(
                file_path=rel_path,
                rule="READ_ERROR",
                message=f"Failed to read file: {exc}",
                remediation_hint="Ensure file is readable UTF-8 text.",
            )
        ]

    meta, _, parse_err = parse_frontmatter(content)
    if parse_err:
        return [
            OkfValidationFinding(
                file_path=rel_path,
                rule="PARSE_ERROR",
                message=parse_err,
                remediation_hint="Ensure frontmatter is valid YAML delimited by '---'.",
            )
        ]

    if meta is None:
        return [
            OkfValidationFinding(
                file_path=rel_path,
                rule="MISSING_FRONTMATTER",
                message="Document has no YAML frontmatter header.",
                remediation_hint="Add '---' block with at least 'type: <Concept Type>' at the top of the file.",
            )
        ]

    return validate_okf_metadata(meta, file_path=rel_path, now=now)


def validate_okf_workspace(
    workspace_root: Path,
    target_paths: Optional[List[str]] = None,
    now: Optional[datetime] = None,
) -> OkfValidationReport:
    """Scan and validate all target documentation files in workspace."""
    root = workspace_root.resolve()
    paths_to_check: List[Path] = []

    if target_paths:
        for p_str in target_paths:
            p = (root / p_str).resolve()
            if p.is_file() and p.suffix.lower() == ".md":
                paths_to_check.append(p)
            elif p.is_dir():
                paths_to_check.extend(sorted(p.rglob("*.md")))
    else:
        # Default monitored scopes in agent-gauntlet
        default_dirs = ["tasks", "docs/adr"]
        default_files = ["spec.md", "CONTEXT.md"]

        for d_str in default_dirs:
            d = root / d_str
            if d.is_dir():
                paths_to_check.extend(sorted(d.rglob("*.md")))

        for f_str in default_files:
            f = root / f_str
            if f.is_file():
                paths_to_check.append(f)

    # De-duplicate while preserving order
    seen = set()
    unique_paths = []
    for p in paths_to_check:
        if p not in seen:
            seen.add(p)
            unique_paths.append(p)

    all_findings: List[OkfValidationFinding] = []
    valid_count = 0

    for path in unique_paths:
        file_findings = validate_okf_file(path, now=now)
        if file_findings:
            all_findings.extend(file_findings)
        else:
            valid_count += 1

    return OkfValidationReport(
        valid=len(all_findings) == 0,
        findings=all_findings,
        total_files=len(unique_paths),
        valid_files=valid_count,
    )

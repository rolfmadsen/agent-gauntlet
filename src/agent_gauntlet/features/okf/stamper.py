"""Tooling for stamping and updating OKF frontmatter without mutating markdown body."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

from agent_gauntlet.features.okf.validator import parse_frontmatter


def stamp_okf_content(
    content: str,
    doc_type: Optional[str] = None,
    status: Optional[str] = None,
    verified_by: Optional[str] = None,
    verified_at: Optional[str] = None,
    generated_by: Optional[str] = None,
    generated_at: Optional[str] = None,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> str:
    """Update or inject OKF frontmatter into Markdown content."""
    meta, body, err = parse_frontmatter(content)
    if meta is None:
        meta = {}

    if doc_type:
        meta["type"] = doc_type
    elif "type" not in meta:
        meta["type"] = "Concept"

    if title:
        meta["title"] = title

    if status:
        meta["status"] = status

    if tags is not None:
        meta["tags"] = tags

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if generated_by:
        gen_entry: Dict[str, Any] = {"by": generated_by}
        gen_entry["at"] = generated_at if generated_at else now_iso
        meta["generated"] = gen_entry

    if verified_by:
        v_at = verified_at if verified_at else now_iso
        v_entry = {"by": verified_by, "at": v_at}
        existing_verified = meta.get("verified")
        if existing_verified is None:
            meta["verified"] = [v_entry]
        elif isinstance(existing_verified, list):
            # Check if this actor already verified at this timestamp
            meta["verified"].append(v_entry)
        elif isinstance(existing_verified, dict):
            meta["verified"] = [existing_verified, v_entry]
        else:
            meta["verified"] = [v_entry]

    # Dump YAML frontmatter cleanly
    yaml_text = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).strip()

    # Format cleanly with delimiters
    body_clean = body.lstrip("\n")
    return f"---\n{yaml_text}\n---\n\n{body_clean}"


def stamp_okf_file(
    file_path: Path,
    doc_type: Optional[str] = None,
    status: Optional[str] = None,
    verified_by: Optional[str] = None,
    verified_at: Optional[str] = None,
    generated_by: Optional[str] = None,
    generated_at: Optional[str] = None,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> None:
    """Stamp or update OKF frontmatter in a file on disk."""
    content = file_path.read_text(encoding="utf-8")
    updated = stamp_okf_content(
        content,
        doc_type=doc_type,
        status=status,
        verified_by=verified_by,
        verified_at=verified_at,
        generated_by=generated_by,
        generated_at=generated_at,
        title=title,
        tags=tags,
    )
    file_path.write_text(updated, encoding="utf-8")

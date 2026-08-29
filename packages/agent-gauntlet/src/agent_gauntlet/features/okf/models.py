"""Data models for Open Knowledge Format (OKF v0.2)."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class StatusEnum(str, Enum):
    DRAFT = "draft"
    STABLE = "stable"
    DEPRECATED = "deprecated"


@dataclass(frozen=True)
class Actor:
    """Actor identity in OKF v0.2 format."""

    kind: str  # 'human', 'agent', 'process'
    identifier: str
    raw: str
    namespace: Optional[str] = None

    @classmethod
    def parse(cls, actor_str: str) -> "Actor":
        """Parse an actor string into a structured Actor object.

        Valid formats:
        - human:<id>
        - <producer>/<version>
        - process:<id>
        """
        if not actor_str or not isinstance(actor_str, str):
            raise ValueError(f"Actor must be a non-empty string, got: {actor_str!r}")

        actor_str = actor_str.strip()

        if actor_str.startswith("human:"):
            identifier = actor_str[6:].strip()
            if not identifier or "/" in identifier:
                raise ValueError(f"Invalid human actor format: {actor_str!r}")
            return cls(kind="human", identifier=identifier, raw=actor_str)

        if actor_str.startswith("process:"):
            identifier = actor_str[8:].strip()
            if not identifier:
                raise ValueError(f"Invalid process actor format: {actor_str!r}")
            return cls(kind="process", identifier=identifier, raw=actor_str)

        if "/" in actor_str:
            parts = actor_str.split("/", 1)
            namespace = parts[0].strip()
            identifier = parts[1].strip()
            if not namespace or not identifier:
                raise ValueError(f"Invalid agent actor format: {actor_str!r}")
            return cls(
                kind="agent",
                identifier=identifier,
                raw=actor_str,
                namespace=namespace,
            )

        raise ValueError(
            f"Invalid actor convention: {actor_str!r}. Must be 'human:<id>', '<producer>/<version>', or 'process:<id>'."
        )


@dataclass
class SourceEntry:
    """A source material in OKF v0.2."""

    resource: str
    id: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    usage_count: Optional[int] = None
    last_modified: Optional[str] = None


@dataclass
class VerifiedEntry:
    """A verification record in OKF v0.2."""

    by: str
    at: str


@dataclass
class GeneratedEntry:
    """Generation metadata in OKF v0.2."""

    by: str
    at: Optional[str] = None


@dataclass
class OkfMetadata:
    """Complete structured OKF v0.2 frontmatter metadata."""

    type: str
    title: Optional[str] = None
    description: Optional[str] = None
    resource: Optional[str] = None
    status: str = StatusEnum.STABLE.value
    tags: List[str] = field(default_factory=list)
    generated: Optional[GeneratedEntry] = None
    verified: List[VerifiedEntry] = field(default_factory=list)
    stale_after: Optional[str] = None
    sources: List[SourceEntry] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OkfValidationFinding:
    """A structured finding emitted by the OKF validator."""

    file_path: str
    rule: str
    message: str
    remediation_hint: str
    line: Optional[int] = None
    severity: str = "ERROR"


@dataclass
class OkfValidationReport:
    """Consolidated report across one or more OKF files."""

    valid: bool
    findings: List[OkfValidationFinding]
    total_files: int
    valid_files: int

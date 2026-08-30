"""Append-only, hash-chained session event log with cryptographic continuity checks."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


class EventLogTamperError(Exception):
    """Raised when event log hash chaining or continuity is broken."""


@dataclass(frozen=True)
class EventLogEntry:
    """Immutable, hash-bound event log entry."""

    index: int
    event_type: str
    timestamp_utc: str
    payload_json: str
    payload_digest: str
    prev_hash: str
    event_hash: str

    def to_dict(self) -> dict[str, Any]:
        """Serializes log entry to dictionary."""
        return asdict(self)


class SessionEventLog:
    """Manages an append-only, tamper-evident hash-chained event log for a session."""

    GENESIS_HASH = "sha256:0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self._entries: list[EventLogEntry] = []
        self._root_hash: str = self.GENESIS_HASH

    @property
    def entries(self) -> list[EventLogEntry]:
        """Returns an immutable copy of event log entries."""
        return list(self._entries)

    def get_root_hash(self) -> str:
        """Returns the current rolling root hash of the log."""
        return self._root_hash

    @staticmethod
    def _compute_hash(
        index: int,
        event_type: str,
        timestamp_utc: str,
        payload_digest: str,
        prev_hash: str,
    ) -> str:
        data = f"{index}\0{event_type}\0{timestamp_utc}\0{payload_digest}\0{prev_hash}"
        return f"sha256:{hashlib.sha256(data.encode('utf-8')).hexdigest()}"

    def append(self, event_type: str, payload: dict[str, Any]) -> EventLogEntry:
        """Appends a new event and updates the hash chain."""
        index = len(self._entries)
        now_utc = datetime.now(timezone.utc).isoformat()
        payload_str = json.dumps(payload, sort_keys=True)
        payload_digest = f"sha256:{hashlib.sha256(payload_str.encode('utf-8')).hexdigest()}"
        prev_hash = self._entries[-1].event_hash if self._entries else "genesis"

        event_hash = self._compute_hash(
            index=index,
            event_type=event_type,
            timestamp_utc=now_utc,
            payload_digest=payload_digest,
            prev_hash=prev_hash,
        )

        entry = EventLogEntry(
            index=index,
            event_type=event_type,
            timestamp_utc=now_utc,
            payload_json=payload_str,
            payload_digest=payload_digest,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
        self._entries.append(entry)
        self._root_hash = event_hash
        return entry

    def verify_integrity(self) -> bool:
        """Verifies hash-chain continuity from index 0 to current root."""
        expected_prev = "genesis"
        for entry in self._entries:
            if entry.prev_hash != expected_prev:
                raise EventLogTamperError(
                    f"Hash chain broken at index {entry.index}: prev_hash '{entry.prev_hash}' != expected '{expected_prev}'"
                )

            # Verify payload digest
            actual_payload_digest = (
                f"sha256:{hashlib.sha256(entry.payload_json.encode('utf-8')).hexdigest()}"
            )
            if actual_payload_digest != entry.payload_digest:
                raise EventLogTamperError(
                    f"Payload digest mismatch at index {entry.index}: '{actual_payload_digest}' != '{entry.payload_digest}'"
                )

            # Verify entry hash
            computed = self._compute_hash(
                index=entry.index,
                event_type=entry.event_type,
                timestamp_utc=entry.timestamp_utc,
                payload_digest=entry.payload_digest,
                prev_hash=entry.prev_hash,
            )
            if computed != entry.event_hash:
                raise EventLogTamperError(
                    f"Event hash mismatch at index {entry.index}: '{computed}' != '{entry.event_hash}'"
                )

            expected_prev = entry.event_hash

        return True

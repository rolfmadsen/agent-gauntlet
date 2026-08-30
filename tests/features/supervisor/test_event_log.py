"""Tests for append-only, hash-chained session event log and tamper detection."""

import unittest

from agent_gauntlet.features.supervisor.core.event_log import (
    EventLogEntry,
    EventLogTamperError,
    SessionEventLog,
)


class TestSessionEventLog(unittest.TestCase):
    """Verifies that the event log maintains cryptographic hash continuity."""

    def setUp(self) -> None:
        self.log = SessionEventLog(session_id="sess-001")

    def test_initial_log_state(self) -> None:
        """New event log has 0 entries and initial genesis root."""
        self.assertEqual(len(self.log.entries), 0)
        self.assertTrue(self.log.get_root_hash().startswith("sha256:"))

    def test_append_event_updates_hash_chain(self) -> None:
        """Appending events updates the rolling root hash and increments index."""
        e1 = self.log.append(event_type="SESSION_START", payload={"task_id": "035-test"})
        self.assertEqual(e1.index, 0)
        self.assertEqual(e1.prev_hash, "genesis")
        self.assertTrue(e1.event_hash.startswith("sha256:"))

        e2 = self.log.append(
            event_type="TOOL_EVALUATION", payload={"tool": "view_file", "verdict": "allow"}
        )
        self.assertEqual(e2.index, 1)
        self.assertEqual(e2.prev_hash, e1.event_hash)
        self.assertEqual(self.log.get_root_hash(), e2.event_hash)

    def test_verify_integrity_succeeds_on_intact_log(self) -> None:
        """Intact event log passes cryptographic integrity verification."""
        self.log.append(event_type="SESSION_START", payload={"task_id": "035-test"})
        self.log.append(event_type="TOOL_EVALUATION", payload={"tool": "view_file"})
        self.log.append(event_type="VERIFICATION_REQUESTED", payload={"snapshot": "snap123"})
        self.assertTrue(self.log.verify_integrity())

    def test_tampered_entry_payload_detected(self) -> None:
        """Tampering with an event payload breaks hash continuity and raises error."""
        self.log.append(event_type="SESSION_START", payload={"task_id": "035-test"})
        self.log.append(
            event_type="TOOL_EVALUATION", payload={"tool": "view_file", "verdict": "allow"}
        )

        # Tamper with internal entry list
        original = self.log._entries[1]
        tampered = EventLogEntry(
            index=original.index,
            event_type=original.event_type,
            timestamp_utc=original.timestamp_utc,
            payload_json='{"tool": "view_file", "verdict": "TAMPERED"}',
            payload_digest="sha256:fake",
            prev_hash=original.prev_hash,
            event_hash=original.event_hash,
        )
        self.log._entries[1] = tampered

        with self.assertRaises(EventLogTamperError):
            self.log.verify_integrity()


if __name__ == "__main__":
    unittest.main()

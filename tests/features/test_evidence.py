"""Black-box acceptance tests for features/evidence_authority."""

import time
import unittest

from agent_gauntlet.features.evidence import (
    CheckSummary,
    EvidenceAuthority,
    EvidenceRecord,
)


class TestEvidenceAuthorityAcceptance(unittest.TestCase):
    """Acceptance tests for EvidenceAuthority."""

    def setUp(self) -> None:
        self.authority = EvidenceAuthority(secret_key=b"test-secret-key-12345")
        self.sample_record = EvidenceRecord(
            task_id="task-test-001",
            status="PASSED",
            source_tree_hash="a1b2c3d4e5f60011",
            checks=[
                CheckSummary(name="unit-tests", passed=True, exit_code=0, duration_seconds=0.12),
                CheckSummary(name="mutation-testing", passed=True, exit_code=0, duration_seconds=1.45),
            ],
            timestamp=1700000000.0,
        )

    def test_signing_and_verification_happy_path(self) -> None:
        """Scenario EA-01: Sign a valid record and verify HMAC signature."""
        signed = self.authority.sign_record(self.sample_record)

        self.assertIsNotNone(signed.signature)
        self.assertIsInstance(signed.signature, str)
        self.assertGreater(len(signed.signature or ""), 16)
        self.assertTrue(self.authority.verify_record(signed))

    def test_tamper_status_fails_verification(self) -> None:
        """Scenario EA-02a: Tampering with status invalidates signature."""
        failed_record = EvidenceRecord(
            task_id="task-test-001",
            status="FAILED",
            source_tree_hash="a1b2c3d4e5f60011",
            checks=[CheckSummary(name="unit-tests", passed=False, exit_code=1)],
            timestamp=1700000000.0,
        )
        signed = self.authority.sign_record(failed_record)

        tampered = EvidenceRecord(
            task_id=signed.task_id,
            status="PASSED",  # Maliciously altered
            source_tree_hash=signed.source_tree_hash,
            checks=signed.checks,
            timestamp=signed.timestamp,
            signature=signed.signature,
        )
        self.assertFalse(self.authority.verify_record(tampered))

    def test_tamper_checks_fails_verification(self) -> None:
        """Scenario EA-02b: Tampering with check details invalidates signature."""
        signed = self.authority.sign_record(self.sample_record)

        tampered_checks = [
            CheckSummary(name="unit-tests", passed=True, exit_code=0, duration_seconds=0.12),
            CheckSummary(name="mutation-testing", passed=False, exit_code=1, duration_seconds=1.45),
        ]
        tampered = EvidenceRecord(
            task_id=signed.task_id,
            status=signed.status,
            source_tree_hash=signed.source_tree_hash,
            checks=tampered_checks,
            timestamp=signed.timestamp,
            signature=signed.signature,
        )
        self.assertFalse(self.authority.verify_record(tampered))

    def test_tamper_tree_hash_fails_verification(self) -> None:
        """Scenario EA-02c: Tampering with tree hash invalidates signature."""
        signed = self.authority.sign_record(self.sample_record)

        tampered = EvidenceRecord(
            task_id=signed.task_id,
            status=signed.status,
            source_tree_hash="deadbeef00000000",
            checks=signed.checks,
            timestamp=signed.timestamp,
            signature=signed.signature,
        )
        self.assertFalse(self.authority.verify_record(tampered))

    def test_unsigned_record_fails_verification(self) -> None:
        """Scenario EA-05: Unsigned record returns False without crashing."""
        self.assertFalse(self.authority.verify_record(self.sample_record))

    def test_source_state_match_and_drift(self) -> None:
        """Scenario EA-03: Verify source tree hash match and drift detection."""
        signed = self.authority.sign_record(self.sample_record)

        self.assertTrue(
            self.authority.verify_source_state_match(signed, "a1b2c3d4e5f60011"),
            "Matching tree hash must pass verification",
        )
        self.assertFalse(
            self.authority.verify_source_state_match(signed, "ffffffffffffffff"),
            "Drifted tree hash must fail verification",
        )

    def test_source_state_match_fails_on_tampered_signature(self) -> None:
        """Scenario EA-03b: Matching tree hash fails if record signature is tampered."""
        signed = self.authority.sign_record(self.sample_record)
        tampered = EvidenceRecord(
            task_id=signed.task_id,
            status="FAILED",  # Tampered
            source_tree_hash=signed.source_tree_hash,
            checks=signed.checks,
            timestamp=signed.timestamp,
            signature=signed.signature,
        )
        self.assertFalse(
            self.authority.verify_source_state_match(tampered, signed.source_tree_hash),
            "Tampered record must fail source state verification even if tree hash matches",
        )

    def test_json_roundtrip(self) -> None:
        """Scenario EA-04a: JSON serialization and deserialization roundtrip."""
        signed = self.authority.sign_record(self.sample_record)
        json_str = self.authority.generate_evidence_json(signed)

        loaded = EvidenceAuthority.load_evidence_json(json_str)
        self.assertEqual(loaded.task_id, signed.task_id)
        self.assertEqual(loaded.status, signed.status)
        self.assertEqual(loaded.source_tree_hash, signed.source_tree_hash)
        self.assertEqual(loaded.signature, signed.signature)
        self.assertEqual(len(loaded.checks), len(signed.checks))
        self.assertTrue(self.authority.verify_record(loaded))

    def test_markdown_generation(self) -> None:
        """Scenario EA-04b: Markdown rendering contains required metadata and table."""
        signed = self.authority.sign_record(self.sample_record)
        md = self.authority.generate_evidence_markdown(
            signed,
            head="31211f4",
            source_commit="31211f4",
            title="Bootstrap Evidence",
        )

        self.assertIn("# Bootstrap Evidence", md)
        self.assertIn("task-test-001", md)
        self.assertIn("PASSED", md)
        self.assertIn("a1b2c3d4e5f60011", md)
        self.assertIn(signed.signature or "", md)
        self.assertIn("unit-tests", md)
        self.assertIn("mutation-testing", md)

    def test_task_bound_evidence_tampering_fails(self) -> None:
        """Scenario EA-05: Tampering with task_title or acceptance_criteria invalidates signature."""
        task_record = EvidenceRecord(
            task_id="task-004",
            task_title="Surgical Hook",
            acceptance_criteria=["Criterion 1", "Criterion 2"],
            unresolved_criteria=["Criterion 2"],
            status="PASSED",
            source_tree_hash="a1b2c3d4e5f60011",
            checks=[CheckSummary(name="unit", passed=True, exit_code=0, duration_seconds=0.1)],
            timestamp=1700000000.0,
        )
        signed = self.authority.sign_record(task_record)
        self.assertTrue(self.authority.verify_record(signed))

        # Tamper with task title
        tampered_title = EvidenceRecord(
            task_id=signed.task_id,
            task_title="Fake Title",
            acceptance_criteria=signed.acceptance_criteria,
            unresolved_criteria=signed.unresolved_criteria,
            status=signed.status,
            source_tree_hash=signed.source_tree_hash,
            checks=signed.checks,
            timestamp=signed.timestamp,
            signature=signed.signature,
        )
        self.assertFalse(self.authority.verify_record(tampered_title))

        # Tamper with acceptance criteria
        tampered_criteria = EvidenceRecord(
            task_id=signed.task_id,
            task_title=signed.task_title,
            acceptance_criteria=["Falsified Criteria"],
            unresolved_criteria=signed.unresolved_criteria,
            status=signed.status,
            source_tree_hash=signed.source_tree_hash,
            checks=signed.checks,
            timestamp=signed.timestamp,
            signature=signed.signature,
        )
        self.assertFalse(self.authority.verify_record(tampered_criteria))

    def test_json_and_markdown_with_task_criteria(self) -> None:
        """Scenario EA-06: Task criteria roundtrip in JSON and render in Markdown."""
        task_record = EvidenceRecord(
            task_id="task-004",
            task_title="Surgical Hook",
            acceptance_criteria=["Criterion 1", "Criterion 2"],
            unresolved_criteria=["Criterion 2"],
            status="PASSED",
            source_tree_hash="a1b2c3d4e5f60011",
            checks=[CheckSummary(name="unit", passed=True, exit_code=0, duration_seconds=0.1)],
            timestamp=1700000000.0,
        )
        signed = self.authority.sign_record(task_record)
        json_str = self.authority.generate_evidence_json(signed)
        loaded = EvidenceAuthority.load_evidence_json(json_str)

        self.assertEqual(loaded.task_title, "Surgical Hook")
        self.assertEqual(loaded.acceptance_criteria, ["Criterion 1", "Criterion 2"])
        self.assertEqual(loaded.unresolved_criteria, ["Criterion 2"])
        self.assertTrue(self.authority.verify_record(loaded))

        md = self.authority.generate_evidence_markdown(signed)
        self.assertIn("Surgical Hook", md)
        self.assertIn("- [x] Criterion 1", md)
        self.assertIn("- [ ] Criterion 2", md)


if __name__ == "__main__":
    unittest.main()

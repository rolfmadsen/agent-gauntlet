"""Protected Linux Key Provider managing installation identity and ephemeral task keys."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TaskCertificate:
    """Cryptographically signed task certificate binding session parameters to installation identity."""

    workspace_id: str
    task_id: str
    task_digest: str
    wasm_digest: str
    installation_public_key: str
    task_public_key: str
    issued_at_utc: str
    certificate_signature: str

    def to_dict(self) -> dict[str, Any]:
        """Serializes certificate to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskCertificate:
        """Constructs TaskCertificate from dictionary."""
        return cls(
            workspace_id=str(data.get("workspace_id", "")),
            task_id=str(data.get("task_id", "")),
            task_digest=str(data.get("task_digest", "")),
            wasm_digest=str(data.get("wasm_digest", "")),
            installation_public_key=str(data.get("installation_public_key", "")),
            task_public_key=str(data.get("task_public_key", "")),
            issued_at_utc=str(data.get("issued_at_utc", "")),
            certificate_signature=str(data.get("certificate_signature", "")),
        )


class LinuxKeyProvider:
    """Linux implementation of KeyProviderSeam with strict OS file permissions (0700/0600)."""

    def __init__(self, key_storage_dir: Path | None = None) -> None:
        if key_storage_dir:
            self.storage_dir = Path(key_storage_dir).resolve()
        elif os.environ.get("AGENT_GAUNTLET_KEY_DIR"):
            self.storage_dir = Path(os.environ["AGENT_GAUNTLET_KEY_DIR"]).resolve()
        else:
            base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
            self.storage_dir = (base / "agent-gauntlet" / "keys").resolve()

        self._ensure_storage_dir()
        self._installation_secret = self._load_or_create_installation_secret()
        self._installation_public_key = (
            f"ag_inst_{hashlib.sha256(self._installation_secret).hexdigest()[:32]}"
        )
        self._ephemeral_task_secrets: dict[str, bytes] = {}
        self._ephemeral_task_public_keys: dict[str, str] = {}

    def _ensure_storage_dir(self) -> None:
        """Creates directory with strict 0700 permissions."""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            try:
                os.chmod(self.storage_dir, 0o700)
            except OSError:
                pass
        except OSError:
            import tempfile

            # Use a secure, uniquely generated private directory to prevent symlink/squatting vulnerabilities
            secure_tmp = Path(tempfile.mkdtemp(prefix="agent-gauntlet-keys-"))
            try:
                os.chmod(secure_tmp, 0o700)
            except OSError:
                pass
            self.storage_dir = secure_tmp

    def _load_or_create_installation_secret(self) -> bytes:
        """Loads or creates persistent 256-bit installation secret with 0600 permissions."""
        key_file = self.storage_dir / "installation.key"
        if key_file.is_file():
            return key_file.read_bytes()

        secret = secrets.token_bytes(32)
        key_file.write_bytes(secret)
        try:
            os.chmod(key_file, 0o600)
        except OSError:
            pass
        return secret

    def get_installation_public_key(self) -> str:
        """Returns the persistent installation public key identifier."""
        return self._installation_public_key

    def issue_task_certificate(
        self,
        workspace_id: str,
        task_id: str,
        task_digest: str,
        wasm_digest: str,
    ) -> TaskCertificate:
        """Generates an ephemeral task key and issues an installation-signed TaskCertificate."""
        task_secret = secrets.token_bytes(32)
        self._ephemeral_task_secrets[task_id] = task_secret

        task_public_key = f"ag_task_{hashlib.sha256(task_secret).hexdigest()[:32]}"
        self._ephemeral_task_public_keys[task_id] = task_public_key

        now_utc = datetime.now(timezone.utc).isoformat()
        cert_payload = f"{workspace_id}\0{task_id}\0{task_digest}\0{wasm_digest}\0{self._installation_public_key}\0{task_public_key}\0{now_utc}"

        cert_sig = (
            "sig_"
            + hmac.new(
                self._installation_secret, cert_payload.encode("utf-8"), hashlib.sha256
            ).hexdigest()
        )

        return TaskCertificate(
            workspace_id=workspace_id,
            task_id=task_id,
            task_digest=task_digest,
            wasm_digest=wasm_digest,
            installation_public_key=self._installation_public_key,
            task_public_key=task_public_key,
            issued_at_utc=now_utc,
            certificate_signature=cert_sig,
        )

    def verify_task_certificate(self, cert: TaskCertificate) -> bool:
        """Verifies the validity of a task certificate against the installation identity."""
        if cert.installation_public_key != self._installation_public_key:
            return False

        cert_payload = f"{cert.workspace_id}\0{cert.task_id}\0{cert.task_digest}\0{cert.wasm_digest}\0{cert.installation_public_key}\0{cert.task_public_key}\0{cert.issued_at_utc}"
        expected_sig = (
            "sig_"
            + hmac.new(
                self._installation_secret, cert_payload.encode("utf-8"), hashlib.sha256
            ).hexdigest()
        )
        return hmac.compare_digest(cert.certificate_signature, expected_sig)

    def sign_canonical_report(
        self,
        report_bytes: bytes,
        task_id: str,
    ) -> str:
        """Signs a canonical report using the task ephemeral private key."""
        task_secret = self._ephemeral_task_secrets.get(task_id)
        if not task_secret:
            raise KeyError(f"No ephemeral task secret active for task '{task_id}'")

        return "sig_" + hmac.new(task_secret, report_bytes, hashlib.sha256).hexdigest()

    def verify_report_signature(
        self,
        report_bytes: bytes,
        task_public_key: str,
        signature: str,
    ) -> bool:
        """Verifies report signature against an ephemeral task key secret."""
        # Find matching secret for public key
        matched_secret = None
        for task_id, pub in self._ephemeral_task_public_keys.items():
            if pub == task_public_key:
                matched_secret = self._ephemeral_task_secrets.get(task_id)
                break

        if not matched_secret:
            return False

        expected = "sig_" + hmac.new(matched_secret, report_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)

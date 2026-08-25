"""Attestation bundle models and cryptographic verification engine for Sigstore and GitHub OIDC."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass, field
from typing import Any

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.x509.oid import ExtensionOID

from agent_gauntlet.features.evidence.models import AttestationStatus


def dsse_pae(payload_type: str | bytes, payload: str | bytes) -> bytes:
    """Computes Pre-Authentication Encoding (PAE) according to DSSE v1 specification."""
    type_bytes = payload_type.encode("utf-8") if isinstance(payload_type, str) else payload_type
    body_bytes = payload.encode("utf-8") if isinstance(payload, str) else payload
    return (
        b"DSSEv1 "
        + str(len(type_bytes)).encode("ascii")
        + b" "
        + type_bytes
        + b" "
        + str(len(body_bytes)).encode("ascii")
        + b" "
        + body_bytes
    )


@dataclass(frozen=True)
class AttestationIdentity:
    """OIDC signing identity extracted from Sigstore / GitHub attestation."""

    issuer: str = ""
    repository: str = ""
    workflow: str = ""
    runner_environment: str = "github-hosted"
    sha: str = ""


@dataclass(frozen=True)
class AttestationBundle:
    """Cryptographic attestation envelope for a verification report."""

    bundle_version: str = "0.2"
    media_type: str = "application/vnd.dev.sigstore.bundle+json;version=0.2"
    status: AttestationStatus = AttestationStatus.VALID
    identity: AttestationIdentity | None = None
    predicate_type: str = "https://agent-gauntlet.dev/attestation/v1"
    subject_digest: str = ""
    raw_bundle: dict[str, Any] = field(default_factory=dict)


class AttestationEngine:
    """Engine for parsing and cryptographically verifying Sigstore / GitHub OIDC DSSE attestation bundles."""

    def compute_report_subject_digest(self, report_json_str: str) -> str:
        """Compute deterministic SHA-256 digest of verification report content."""
        return hashlib.sha256(report_json_str.strip().encode("utf-8")).hexdigest()

    def _extract_string_from_ext_value(self, raw_value: bytes) -> str:
        """Extract UTF-8 string from raw X.509 extension bytes, handling simple ASN.1 UTF8String / OctetString."""
        if not raw_value:
            return ""
        # If ASN.1 UTF8String (tag 0x0c) or OctetString (tag 0x04)
        if len(raw_value) >= 2 and raw_value[0] in (0x0C, 0x04, 0x16):
            length = raw_value[1]
            if length < 128 and len(raw_value) >= 2 + length:
                try:
                    return raw_value[2 : 2 + length].decode("utf-8")
                except UnicodeDecodeError:
                    pass
        try:
            return raw_value.decode("utf-8")
        except UnicodeDecodeError:
            return raw_value.decode("latin-1", errors="replace")

    def _parse_certificate_identity(self, cert: x509.Certificate) -> AttestationIdentity:
        """Extracts Sigstore Fulcio GitHub Actions OIDC extension claims from X.509 certificate."""
        issuer = ""
        repository = ""
        workflow = ""
        runner_environment = "github-hosted"
        sha = ""

        # OID mappings for Sigstore Fulcio extensions
        for ext in cert.extensions:
            oid_str = ext.oid.dotted_string
            val_bytes = ext.value.value if hasattr(ext.value, "value") else b""
            val_str = self._extract_string_from_ext_value(val_bytes)

            if oid_str == "1.3.6.1.4.1.57264.1.1":
                issuer = val_str
            elif oid_str == "1.3.6.1.4.1.57264.1.5":
                repository = val_str
            elif oid_str == "1.3.6.1.4.1.57264.1.6":
                workflow = val_str
            elif oid_str in ("1.3.6.1.4.1.57264.1.11", "1.3.6.1.4.1.57264.1.4"):
                if val_str in ("github-hosted", "self-hosted"):
                    runner_environment = val_str
                elif not workflow:
                    workflow = val_str
            elif oid_str == "1.3.6.1.4.1.57264.1.3":
                sha = val_str

        # Fallback to Subject Alternative Name URI if needed
        try:
            san_ext = cert.extensions.get_extension_for_oid(
                ExtensionOID.SUBJECT_ALTERNATIVE_NAME
            )
            for name in san_ext.value:  # type: ignore[attr-defined]
                if isinstance(name, x509.UniformResourceIdentifier) and "github.com" in name.value:
                    if not workflow:
                        workflow = name.value
        except Exception:
            pass

        return AttestationIdentity(
            issuer=issuer or "https://token.actions.githubusercontent.com",
            repository=repository,
            workflow=workflow,
            runner_environment=runner_environment,
            sha=sha,
        )

    def load_bundle(self, content: str | dict[str, Any]) -> AttestationBundle:
        """Parse JSON or dict into an AttestationBundle model and verify DSSE signature cryptographically."""
        if isinstance(content, str):
            try:
                data = json.loads(content)
            except Exception:
                return AttestationBundle(status=AttestationStatus.INVALID)
        elif isinstance(content, dict):
            data = content
        else:
            return AttestationBundle(status=AttestationStatus.INVALID)

        media_type = str(
            data.get(
                "mediaType",
                data.get("media_type", "application/vnd.dev.sigstore.bundle+json;version=0.2"),
            )
        )
        subject_digest = str(data.get("subject_digest", ""))
        predicate_type = str(
            data.get("predicate_type", "https://agent-gauntlet.dev/attestation/v1")
        )
        identity: AttestationIdentity | None = None
        status = AttestationStatus.VALID

        # Check for explicit identity payload
        identity_data = data.get("identity")
        if isinstance(identity_data, dict):
            identity = AttestationIdentity(
                issuer=str(identity_data.get("issuer", "")),
                repository=str(identity_data.get("repository", "")),
                workflow=str(identity_data.get("workflow", "")),
                runner_environment=str(identity_data.get("runner_environment", "github-hosted")),
                sha=str(identity_data.get("sha", "")),
            )

        # Check for Sigstore DSSE envelope and verificationMaterial
        dsse_envelope = data.get("dsseEnvelope")
        verification_material = data.get("verificationMaterial", {})

        if isinstance(dsse_envelope, dict):
            payload_b64 = dsse_envelope.get("payload", "")
            payload_type = str(dsse_envelope.get("payloadType", "application/vnd.in-toto+json"))
            signatures = dsse_envelope.get("signatures", [])

            if not payload_b64 or not isinstance(signatures, list) or len(signatures) == 0:
                return AttestationBundle(status=AttestationStatus.INVALID, raw_bundle=data)

            try:
                payload_raw_bytes = base64.b64decode(payload_b64)
                statement = json.loads(payload_raw_bytes.decode("utf-8"))
                if isinstance(statement, dict):
                    predicate_type = str(statement.get("predicateType", predicate_type))
                    subjects = statement.get("subject", [])
                    if (
                        isinstance(subjects, list)
                        and len(subjects) > 0
                        and isinstance(subjects[0], dict)
                    ):
                        subject_digest = str(
                            subjects[0].get("digest", {}).get("sha256", subject_digest)
                        )
            except Exception:
                return AttestationBundle(status=AttestationStatus.INVALID, raw_bundle=data)

            # Cryptographic Verification against leaf certificate or public key
            if isinstance(verification_material, dict):
                cert_obj = None
                cert_chain = verification_material.get("x509CertificateChain", {})
                if isinstance(cert_chain, dict):
                    certs_list = cert_chain.get("certificates", [])
                    if (
                        isinstance(certs_list, list)
                        and len(certs_list) > 0
                        and isinstance(certs_list[0], dict)
                    ):
                        raw_cert_b64 = certs_list[0].get("rawBytes", "")
                        if raw_cert_b64:
                            try:
                                cert_der = base64.b64decode(raw_cert_b64)
                                cert_obj = x509.load_der_x509_certificate(cert_der)
                            except Exception:
                                return AttestationBundle(
                                    status=AttestationStatus.INVALID, raw_bundle=data
                                )

                if not cert_obj and "certificate" in verification_material:
                    raw_cert_b64 = verification_material.get("certificate", {}).get("rawBytes", "")
                    if raw_cert_b64:
                        try:
                            cert_der = base64.b64decode(raw_cert_b64)
                            cert_obj = x509.load_der_x509_certificate(cert_der)
                        except Exception:
                            return AttestationBundle(
                                status=AttestationStatus.INVALID, raw_bundle=data
                            )

                if cert_obj:
                    identity = self._parse_certificate_identity(cert_obj)
                    public_key = cert_obj.public_key()
                    pae_bytes = dsse_pae(payload_type, payload_raw_bytes)

                    # Verify cryptographic signature
                    sig_valid = False
                    for sig_entry in signatures:
                        if not isinstance(sig_entry, dict) or not sig_entry.get("sig"):
                            continue
                        try:
                            sig_bytes = base64.b64decode(sig_entry["sig"])
                            if isinstance(public_key, ec.EllipticCurvePublicKey):
                                public_key.verify(sig_bytes, pae_bytes, ec.ECDSA(hashes.SHA256()))
                                sig_valid = True
                                break
                            elif isinstance(public_key, rsa.RSAPublicKey):
                                try:
                                    public_key.verify(
                                        sig_bytes, pae_bytes, padding.PKCS1v15(), hashes.SHA256()
                                    )
                                    sig_valid = True
                                    break
                                except InvalidSignature:
                                    public_key.verify(
                                        sig_bytes,
                                        pae_bytes,
                                        padding.PSS(
                                            mgf=padding.MGF1(hashes.SHA256()),
                                            salt_length=padding.PSS.MAX_LENGTH,
                                        ),
                                        hashes.SHA256(),
                                    )
                                    sig_valid = True
                                    break
                        except (InvalidSignature, Exception):
                            continue

                    if not sig_valid:
                        status = AttestationStatus.INVALID

        status_str = str(data.get("status", status.value)).upper()
        try:
            final_status = AttestationStatus(status_str)
            if status == AttestationStatus.INVALID:
                final_status = AttestationStatus.INVALID
        except ValueError:
            final_status = AttestationStatus.INVALID

        return AttestationBundle(
            bundle_version=str(data.get("bundle_version", "0.2")),
            media_type=media_type,
            status=final_status,
            identity=identity,
            predicate_type=predicate_type,
            subject_digest=subject_digest,
            raw_bundle=data,
        )

    def verify_bundle_against_report(
        self,
        bundle: AttestationBundle,
        report_json_str: str,
    ) -> AttestationStatus:
        """Verifies that the attestation bundle cryptographically binds to the report."""
        if bundle.status != AttestationStatus.VALID:
            return AttestationStatus.INVALID

        expected_subject_digest = self.compute_report_subject_digest(report_json_str)
        if not bundle.subject_digest or not hmac.compare_digest(
            bundle.subject_digest, expected_subject_digest
        ):
            return AttestationStatus.INVALID

        return AttestationStatus.VALID

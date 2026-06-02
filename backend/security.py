"""
Demo-only request signing helpers for local RBAC enforcement.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


DEMO_KEY_SCHEME = "ed25519-demo"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def build_signed_message(
    action: str,
    node_id: str,
    timestamp: str,
    nonce: str,
    payload: Mapping[str, Any],
) -> str:
    message = {
        "action": action,
        "node_id": node_id,
        "timestamp": timestamp,
        "nonce": nonce,
        "payload": dict(payload),
    }
    return canonical_json(message)


def verify_signature(public_key_hex: str, message: str, signature_hex: str) -> bool:
    try:
        public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
        public_key.verify(bytes.fromhex(signature_hex), message.encode("utf-8"))
        return True
    except (ValueError, InvalidSignature):
        return False
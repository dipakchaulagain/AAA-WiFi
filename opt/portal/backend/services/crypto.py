from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _b64e(b: bytes) -> str:
    return base64.b64encode(b).decode("utf-8")


def _b64d(s: str) -> bytes:
    return base64.b64decode(s.encode("utf-8"))


def encrypt_aes_gcm(plaintext: str, key_bytes: bytes) -> str:
    nonce = os.urandom(12)
    aes = AESGCM(key_bytes)
    ct = aes.encrypt(nonce, plaintext.encode("utf-8"), None)
    return _b64e(nonce + ct)


def decrypt_aes_gcm(b64_blob: str, key_bytes: bytes) -> str:
    raw = _b64d(b64_blob)
    nonce, ct = raw[:12], raw[12:]
    aes = AESGCM(key_bytes)
    pt = aes.decrypt(nonce, ct, None)
    return pt.decode("utf-8")


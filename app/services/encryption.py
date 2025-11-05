import base64
import os
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings


def _get_key() -> bytes:
    try:
        return base64.b64decode(settings.encryption_key_b64)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Invalid base64 encryption key") from exc


def encrypt_bytes(plaintext: bytes) -> Tuple[bytes, bytes]:
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return nonce, ciphertext


def decrypt_bytes(nonce: bytes, ciphertext: bytes) -> bytes:
    key = _get_key()
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)


def encrypt_text(plaintext: str) -> dict:
    nonce, ct = encrypt_bytes(plaintext.encode("utf-8"))
    return {
        "nonce_b64": base64.b64encode(nonce).decode(),
        "ciphertext_b64": base64.b64encode(ct).decode(),
    }


def decrypt_text(nonce_b64: str, ciphertext_b64: str) -> str:
    nonce = base64.b64decode(nonce_b64)
    ct = base64.b64decode(ciphertext_b64)
    pt = decrypt_bytes(nonce, ct)
    return pt.decode("utf-8")


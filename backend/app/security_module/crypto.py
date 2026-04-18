from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet


def derive_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


class LocalEncryptor:
    def __init__(self, secret: str) -> None:
        self._fernet = Fernet(derive_fernet_key(secret))

    def encrypt_text(self, text: str) -> bytes:
        return self._fernet.encrypt(text.encode("utf-8"))

    def decrypt_text(self, blob: bytes) -> str:
        return self._fernet.decrypt(blob).decode("utf-8")

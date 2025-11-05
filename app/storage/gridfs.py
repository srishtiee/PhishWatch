from typing import Optional
import base64
from bson import ObjectId
from gridfs import GridFS
from app.db.mongo import get_sync_gridfs
from app.services.encryption import encrypt_bytes, decrypt_bytes


class EncryptedGridFS:
    def __init__(self, fs: Optional[GridFS] = None) -> None:
        self.fs = fs or get_sync_gridfs()

    def put(self, data: bytes, filename: str | None = None, content_type: str | None = None) -> ObjectId:
        nonce, ciphertext = encrypt_bytes(data)
        oid = self.fs.put(
            ciphertext,
            filename=filename,
            content_type=content_type,
            metadata={"nonce_b64": base64.b64encode(nonce).decode()},
        )
        return oid

    def get(self, oid: ObjectId) -> bytes:
        f = self.fs.get(oid)
        nonce_b64 = f.metadata.get("nonce_b64") if f.metadata else None
        if not nonce_b64:
            raise ValueError("Missing nonce for encrypted file")
        nonce = base64.b64decode(nonce_b64)
        ciphertext = f.read()
        return decrypt_bytes(nonce, ciphertext)


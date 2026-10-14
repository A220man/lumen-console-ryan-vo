import base64
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core.config import get_settings

settings = get_settings()


def get_encryption_key() -> bytes:
    key = settings.encryption_key.strip()
    if not key:
        if settings.demo_mode:
            return b"0" * 32
        raise ValueError("ENCRYPTION_KEY must be set in production")
    decoded = base64.b64decode(key)
    if len(decoded) != 32:
        raise ValueError("ENCRYPTION_KEY must be 32 bytes (base64 encoded)")
    return decoded


def encrypt_token(plaintext: str) -> str:
    key = get_encryption_key()
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode()


def decrypt_token(ciphertext_b64: str) -> str:
    key = get_encryption_key()
    aesgcm = AESGCM(key)
    data = base64.b64decode(ciphertext_b64)
    nonce, ciphertext = data[:12], data[12:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode()


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def generate_nonce() -> str:
    return secrets.token_urlsafe(32)


def generate_pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)[:128]
    import hashlib
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).decode().rstrip("=")
    return verifier, challenge
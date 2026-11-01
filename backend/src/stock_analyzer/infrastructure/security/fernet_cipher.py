"""Fernet (AES-128-CBC + HMAC) encryption with ``SA_MASTER_KEY``."""

from cryptography.fernet import Fernet, InvalidToken

from stock_analyzer.application.errors import ConfigurationError


class FernetCipher:
    """Implements ``SecretCipher``; an empty master key disables storing secrets."""

    def __init__(self, master_key: str) -> None:
        """Use ``master_key`` (a urlsafe base64 32-byte Fernet key)."""
        self._fernet = Fernet(master_key.encode()) if master_key else None

    @property
    def is_configured(self) -> bool:
        """Whether a master key is set."""
        return self._fernet is not None

    def _require(self) -> Fernet:
        if self._fernet is None:
            raise ConfigurationError("SA_MASTER_KEY is not set: run `make bootstrap` first")
        return self._fernet

    def encrypt(self, plaintext: str) -> bytes:
        """Return the Fernet token for ``plaintext``."""
        return self._require().encrypt(plaintext.encode())

    def decrypt(self, ciphertext: bytes) -> str:
        """Return the plaintext; a different master key raises ``ConfigurationError``."""
        try:
            return self._require().decrypt(ciphertext).decode()
        except InvalidToken as error:
            raise ConfigurationError(
                "stored secret can't be decrypted: SA_MASTER_KEY changed?"
            ) from error

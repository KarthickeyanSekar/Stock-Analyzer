"""Secret encryption port (provider credentials are stored encrypted, CLAUDE.md)."""

from typing import Protocol


class SecretCipher(Protocol):
    """Symmetric encryption for secrets at rest."""

    @property
    def is_configured(self) -> bool:
        """Whether a master key is set (secrets can't be stored without one)."""
        ...

    def encrypt(self, plaintext: str) -> bytes:
        """Return the ciphertext."""
        ...

    def decrypt(self, ciphertext: bytes) -> str:
        """Return the plaintext; raises if the key doesn't match."""
        ...

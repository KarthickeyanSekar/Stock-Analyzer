"""Application-level errors (mapped to HTTP responses by the presentation layer)."""

from stock_analyzer.domain.shared.errors import DomainError


class NotFoundError(DomainError):
    """Raised when a requested stock, plan or provider does not exist."""


class ConfigurationError(DomainError):
    """Raised when a required setting or credential is missing or unusable."""


class ProviderError(DomainError):
    """Raised when a data provider rejects a request or is unreachable (message has no secrets)."""


class AuthError(DomainError):
    """Sign-in failed or the session is not valid; the message is safe to show."""


class ForbiddenError(DomainError):
    """The signed-in user may not do this."""

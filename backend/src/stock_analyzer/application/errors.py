"""Application-level errors (mapped to HTTP responses by the presentation layer)."""

from stock_analyzer.domain.shared.errors import DomainError


class NotFoundError(DomainError):
    """Raised when a requested stock, plan or provider does not exist."""

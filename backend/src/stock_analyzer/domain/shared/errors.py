"""Base class for every business-rule violation."""


class DomainError(Exception):
    """Raised when a business rule is broken; mapped to an HTTP 4xx by the presentation layer."""

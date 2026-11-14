"""Auth-related control-flow exceptions."""


class NotAuthenticated(Exception):
    """Raised when a login is required; handled by redirecting to /login."""


class EngagementRequired(Exception):
    """Raised when an engagement context is required."""

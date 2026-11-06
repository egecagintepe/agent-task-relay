"""Exception classes for Agent Task Relay."""


class RelayError(Exception):
    """Base exception for all Agent Task Relay errors."""
    pass


class ConfigurationError(RelayError):
    """Raised when configuration is missing, unreadable, or invalid."""
    pass


class TransportError(RelayError):
    """Raised when Git or bridge transport operations fail."""
    pass


class TaskValidationError(RelayError):
    """Raised when task packet fails validation (ID format, size, structure)."""
    pass


class StateTransitionError(RelayError):
    """Raised when an illegal task state transition is attempted."""
    pass


class SecurityError(RelayError):
    """Raised when security boundaries (paths, symlinks, approvals) are breached."""
    pass


class RunnerError(RelayError):
    """Raised when a coding-agent runner fails, times out, or behaves unexpectedly."""
    pass


class LockError(RelayError):
    """Raised when the process cannot acquire or release the working lock."""
    pass

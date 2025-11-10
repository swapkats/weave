"""Custom exceptions for Weave."""


class WeaveError(Exception):
    """Base exception for all Weave errors."""

    pass


class ConfigError(WeaveError):
    """Configuration parsing or validation error."""

    pass


class GraphError(WeaveError):
    """Dependency graph error (cycles, invalid structure, etc)."""

    pass


class ExecutionError(WeaveError):
    """Runtime execution error."""

    pass

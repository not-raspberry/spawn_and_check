"""Executor exceptions."""


class ExecutorError(Exception):

    """Raised when cannot execute a command."""


class ChecksFailed(ExecutorError):

    """Raised when checks fail."""


class PreChecksFailed(ChecksFailed):

    """Raised when the pre-execution checks fail."""


class PostChecksFailed(ChecksFailed):

    """Raised when post-execution checks fail."""


class SubprocessExited(ExecutorError):

    """Raised if a process ended before all post-checks went OK."""

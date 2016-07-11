"""Exceptions raised by the ``spawn_and_check.execute`` function."""
from spawn_and_check.polling import TimedOut


class ExecutorError(Exception):

    """Raised when cannot execute a command."""


class ChecksFailed(ExecutorError):

    """Raised when checks fail."""


class PreChecksFailed(ChecksFailed, TimedOut):

    """Raised when the pre-execution checks fail."""


class PostChecksFailed(ChecksFailed, TimedOut):

    """Raised when the post-execution checks fail."""


class CannotTerminate(ChecksFailed, TimedOut):

    """Raised when it's not possible to terminate the process."""


class SubprocessExited(ExecutorError):

    """Raised if a process ended before all post-checks went OK."""

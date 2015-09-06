"""An utility to run checks repeatedly."""
from time import sleep, time
from collections import Callable

from spawn_and_check.constants import DEFAULT_INTERVAL, DEFAULT_TIMEOUT


class TimedOut(Exception):

    """Raised when polling times out."""


def execute_checks(checks):
    """
    Execute all provided checks and return failing ones.

    :param list checks: list of check functions
    :rtype: list
    :return: list of failing check functions
    """
    return [check for check in checks if not check()]


def wait_until(check_functions, interval=DEFAULT_INTERVAL, timeout=DEFAULT_TIMEOUT, sleep_fn=sleep):
    """
    Poll ``check_functions`` until it returns True.

    Assuming ``check_functions`` are well-behaved (they all execute within ``interval`` seconds), they will be called
    repeatedly, every ``interval`` seconds, until all return True or the overall polling duration exceeds ``timeout``.

    All check functions will be called at least once, even if the ``timeout`` is lower than the time all checks execute
    in.

    :param (list, function) check_functions: check functions to poll, should return True if check's condition has been
        met. All checks should not take more time than the ``interval`` to execute. For convenience, if a function is
        provided instead of a list, it is treated as a check functions list with a single check.
    :param float interval: max sleep interval between the checks
    :param float timeout: polling time limit
    :param function sleep: function to use to sleep for a period
    :raise TimedOut: in case of a timeout
    """
    if isinstance(check_functions, Callable):
        # Single check was provided instead of a list.
        check_functions = [check_functions]

    start = time()
    while True:
        time_before_check = time()
        failing_checks = execute_checks(check_functions)
        if not failing_checks:
            return

        if time() > start + timeout:
            raise TimedOut('Timed out polling the checks.', failing_checks)

        time_after_check = time()
        check_duration = time_after_check - time_before_check
        sleep_fn(max(0, interval - check_duration))

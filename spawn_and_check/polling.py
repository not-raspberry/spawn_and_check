"""An utility to run checks repeatedly."""
from time import sleep, time


DEFAULT_INTERVAL = 0.1
DEFAULT_TIMEOUT = 5


class TimedOut(Exception):

    """Raised when polling times out."""


def wait_until(fn, interval=DEFAULT_INTERVAL, timeout=DEFAULT_TIMEOUT, exception=TimedOut, sleep=sleep):
    """
    Poll ``fn`` until it returns True.

    Assuming ``fn`` is well-behaved (executes within ``interval`` seconds), it will be called repeatedly, every
    ``interval`` seconds, until it returns True or the overall polling duration exceeds ``timeout``.

    The function will be called at least once, even if the ``timeout`` is lower than the time ``fn`` executes in.

    :param function fn: check function to poll, should return True if its condition has been met. Should not take more
        time than the ``interval`` to execute.
    :param float interval: max sleep interval between the checks
    :param float timeout: polling time limit
    :param TimedOut exception: exception to raise in case of a timeout, should be derived from TimedOut
    :param function sleep: function to use to sleep for a period
    :raise TimedOut: (or derived exception) in case of a timeout
    """
    start = time()
    while True:
        time_before_check = time()
        status = fn()
        if status is True:
            return

        if time() > start + timeout:
            raise TimedOut('Timed out polling the function.', fn)

        time_after_check = time()
        check_duration = time_after_check - time_before_check
        sleep(max(0, interval - check_duration))

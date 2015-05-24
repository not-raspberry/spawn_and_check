"""Polling utility."""
from time import sleep, time


DEFAULT_INTERVAL = 0.1
DEFAULT_TIMEOUT = 5


class TimedOut(Exception):

    """Raised when polling times out."""


def wait_until(fn, interval=DEFAULT_INTERVAL, timeout=DEFAULT_TIMEOUT):
    """Poll ``fn`` until it returns True."""
    start = time()
    while True:
        status = fn()
        if status is True:
            break
        if time() > start + timeout:
            raise TimedOut('Timed out polling the function.', fn)
        sleep(interval)

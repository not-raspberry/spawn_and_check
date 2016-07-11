"""
Functions to kill subprocesses.

``os.killpg`` is be used to better support multiple processes.

The parent process exiting on its own at any moment is accepted and treated
the same way as if it was killed successully.
"""
import errno
import time
from signal import SIGKILL, SIGTERM
from os import killpg
from spawn_and_check.polling import TimedOut, wait_until
from spawn_and_check.constants import DEFAULT_INTERVAL, DEFAULT_TIMEOUT
from spawn_and_check.exceptions import CannotTerminate


def killpg_if_alive(group_id, signal):
    """
    Send the specified signal to the process group.

    Inability to find the process group will be tolerated, as processes may terminate
    on their own.

    :param int group_id: process group ID to send a signal to (normally parent PID)
    :param int signal: signal to send
    """
    try:
        killpg(group_id, signal)
    except OSError as e:
        if e.errno == errno.ESRCH:  # No such process - might have terminated.
            return
        raise


def killpg_and_check(process, signal, interval=DEFAULT_INTERVAL,
                     timeout=DEFAULT_TIMEOUT, sleep_fn=time.sleep):
    """
    Send a signal to the process group and wait the parent process terminates.

    The parent process exiting on its own at any moment is accepted.

    :param subprocess.Popen process: process to kill
    :param float interval: time to sleep between termination status checks
    :param float timeout: time limit to wait for graceful termination
    :param function sleep_fn: function to sleep
    :raise CannotTerminate: if the process won't terminate
    """
    killpg_if_alive(process.pid, signal)
    try:
        wait_until(lambda: process.poll() is not None,
                   timeout=timeout, interval=interval, sleep_fn=sleep_fn)
    except TimedOut:
        raise CannotTerminate(
            'Process failed to shut down after sending signal {}.'.format(signal),
            process)


def terminate_gracefully(process, signal=SIGTERM, interval=DEFAULT_INTERVAL,
                         timeout=DEFAULT_TIMEOUT, sleep_fn=time.sleep):
    """
    Try to terminate the process gracefully, if the process won't terminate, send SIGKILL.

    The parent process exiting on its own at any moment is accepted.

    :param subprocess.Popen process: process to kill
    :param int signal: signal to terminate gracefully (default: ``signal.SIGTERM``)
    :param float interval: time to sleep between termination status checks
    :param float timeout: time limit to wait for graceful termination
    :param function sleep_fn: function to sleep
    """
    try:
        killpg_and_check(process, signal,
                         timeout=timeout, interval=interval, sleep_fn=sleep_fn)
    except CannotTerminate:
        killpg_and_check(process, SIGKILL,
                         timeout=timeout, interval=interval, sleep_fn=sleep_fn)


def kill_crudely(process, interval=DEFAULT_INTERVAL, timeout=DEFAULT_TIMEOUT,
                 sleep_fn=time.sleep):
    """
    Terminate the process group with SIGKILL and wait for parent process' termination.

    The parent process exiting on its own at any moment is accepted.

    :param subprocess.Popen process: process to kill
    :param float interval: time to sleep between termination status checks
    :param float timeout: time limit to wait for graceful termination
    :param function sleep_fn: function to sleep
    """
    killpg_and_check(process, SIGKILL,
                     timeout=timeout, interval=interval, sleep_fn=sleep_fn)

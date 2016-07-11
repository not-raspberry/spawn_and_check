"""
Command executor.

The point is to run the command and report the process is OK as fast as possible.

With one check the thing is simple - just check repeatedly. If the check is particulary I/O or CPU-intensive,
add some sleep to leave more resources for the booting application.

With multiple check functions, we call them sequentially.
"""
import os
import time
import shlex
import subprocess
import logging
from functools import wraps

from spawn_and_check.exceptions import PreChecksFailed, PostChecksFailed, SubprocessExited
from spawn_and_check.polling import TimedOut, wait_until
from spawn_and_check.killers import terminate_gracefully
from spawn_and_check.constants import DEFAULT_INTERVAL, DEFAULT_TIMEOUT


log = logging.getLogger(__name__)


def negated(fn):
    """
    Create a negated check function and set its metadata.

    :param function fn: function to create a negated version of
    :rtype: function
    :return: negated ``fn``
    """
    @wraps(fn)
    def negated_fn(*args, **kwargs):
        return not fn(*args, **kwargs)

    # If the function name is 'check_tcp', that would be stupid to have a negated function with the same name.
    negated_fn.__name__ = 'negated_' + negated_fn.__name__
    # Same for the docstring.
    negated_fn.__doc__ = 'Call ``%s`` and return negated return value of it.' % fn.__name__

    return negated_fn


def parse_command(command):
    """
    Normalize the command to a list of arguments.

    If the command is a string, parse it to a list using shlex. If a list - return it. If the command is None, raise
    an exception.
    Unicode behaviour will depend on your shell.

    :param (basestring, list) command: shell command to execute
    :raise ValueError: if None was passed instead of a command, which wold trigger a de-facto bug in ``shlex``
    """
    if command is None:
        # We would normally assume the user of the function passes the right types but for this one we'll make
        # an exception. The behaviour of `shlex.split`, when passed a string is normal, but when passed None,
        # it reads from standard input. Let's try not to think why such a strange behaviour was coded into the standard
        # library.
        raise ValueError('The command is None and that would cause shlex.split to read standard input.')

    if isinstance(command, basestring):
        command = shlex.split(command)

    return command


def execute(command,
            checks, pre_checks=None,
            kill_fn=terminate_gracefully,
            interval=DEFAULT_INTERVAL, timeout=DEFAULT_TIMEOUT,
            sleep_fn=time.sleep, popen=subprocess.Popen):
    """
    Fire pre-checks, run the command and fire post-checks.

    Before running the command, pre-checks are executed to ensure that the environment is clean.
    This is useful because if you try to run the same service twice, the second invocation may fail
    (e.g. due to a port being occupied) while the checks succeed because they detect the existing
    service.

    The purpose of post-checks (``checks``) is to ensure e.g. that the application ran by the
    command fully started (e.g. opened an HTTP service, wrote 'Ready' to logs, etc.).  The command
    is ran through ``subprocess.Popen`` and while polling the checks, the ``subprocess.Popen``
    object is checked for the exit status of the command. If the command exits, it counts as a
    failure to start the app.

    :param (str, list) command: shell command to pass to ``subprocess.Popen``. If it is a string,
        will be parsed into a list with ``shlex.split``.
    :param list checks: list of check functions (signature: () -> bool)
    :param (list, NoneType) pre_checks: list of checks fire before the command. If None, negated
        ``checks`` functions will be used. They should return True if the command is clear to
        execute.
    :param float interval: time to sleep between checks
    :param float timeout: time limit for pre-checks, post-checks and killers
    :param function sleep_fn: function to sleep, ``time.sleep`` by default. Pass ``gevent.sleep``
        when working in the gevent environment.
    :param type popen: thingy to use in place of ``subprocess.Popen``. Feel free to pass
        a ``functools.partial`` on ``subprocess.Popen`` that feeds some arguments.
        ``popen`` will be called with the passed ``command`` and ``preexec_fn=os.setsid`` to set
        a new group ID for the spawned process to make killing processes that spawn their children
        easier. The latter also makes it crash under Windows.
    :rtype: subprocess.Popen
    :return: process handle
    :raise PreChecksFailed: if pre-checks failed
    :raise PostChecksFailed: if post-checks kept failing until the polling timed out
    :raise SubprocessExited: if the process exited during the polling
    """
    popen_command = parse_command(command)

    if pre_checks is None:
        pre_checks = map(negated, checks)

    try:
        wait_until(pre_checks, timeout=timeout, interval=interval, sleep_fn=sleep_fn)
    except TimedOut as e:
        raise PreChecksFailed(
            'Pre-checks failed. Check for remains of the previously executed similar process.',
            popen_command, e)

    process = popen(popen_command, preexec_fn=os.setsid)

    def check_if_process_is_still_running():
        """Check if the process exited - if it did, raise an exception to immediately terminate the polling loop."""
        return_code = process.poll()  # Check if exited.
        if return_code is not None:
            raise SubprocessExited('The process exited with %s' % return_code, return_code)
        return True

    try:
        wait_until(checks + [check_if_process_is_still_running], timeout=timeout, interval=interval, sleep_fn=sleep_fn)
    except TimedOut as e:
        kill_fn(process)
        raise PostChecksFailed(popen_command, 'Post-checks failed.', e)

    return process

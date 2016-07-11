"""Killing functions tests."""
import os
import signal
from select import select
import subprocess
import pytest


from spawn_and_check.killers import (
    killpg_if_alive, killpg_and_check, terminate_gracefully, kill_crudely)
from spawn_and_check.exceptions import CannotTerminate


@pytest.fixture
def invalid_pid():
    """
    Return a PID not backed by any process.

    The strategy is to spawn a process and wait for its termination.
    The assumption is made that the PIDs of recently terminated processes
    won't be reused in short time.
    """
    process = subprocess.Popen(['true'])
    process.wait()
    return process.pid


@pytest.fixture
def running_process():
    """Return a subprocess running forever."""
    return subprocess.Popen(['sleep', 'infinity'], preexec_fn=os.setsid)


@pytest.fixture
def process_ignoring_signals():
    """Return a subprocess running forever and ignoring SIGTERM and SIGABRT."""
    process = subprocess.Popen(['./test/fake_service/ignore_signals_and_idle.py'],
                               stdout=subprocess.PIPE, preexec_fn=os.setsid)

    # Wait until the stdout is readable (blocks otherwise).
    select([process.stdout], [], [])

    while True:  # Cannot use ``for line in process.stdout:``- it blocks.
        line = process.stdout.readline()
        if 'Ignoring signals since now!' in line:
            return process


@pytest.mark.parametrize('signal_to_send', [signal.SIGTERM, signal.SIGINT, signal.SIGKILL])
def test_killpg_if_alive(invalid_pid, running_process, signal_to_send):
    """Ensure ``killpg_if_alive`` accepts invalid PIDs and kills passed processes."""
    killpg_if_alive(invalid_pid, signal=signal_to_send)
    killpg_if_alive(running_process.pid, signal=signal_to_send)
    assert running_process.wait() == -signal_to_send


def test_killpg_and_check(running_process, process_ignoring_signals):
    """Ensure ``killpg_and_check`` will raise an exception if the process does not terminate."""
    killpg_and_check(running_process, signal.SIGTERM)
    assert running_process.returncode == -signal.SIGTERM

    with pytest.raises(CannotTerminate):
        killpg_and_check(process_ignoring_signals, signal.SIGTERM, timeout=1)


@pytest.mark.parametrize('signal_to_send', [signal.SIGTERM, signal.SIGABRT])
def test_terminate_gracefully(running_process, process_ignoring_signals, signal_to_send):
    """Ensure that ``terminate_gracefully`` first tries a nice termination method."""
    terminate_gracefully(running_process, signal=signal_to_send)
    assert running_process.returncode == -signal_to_send

    terminate_gracefully(process_ignoring_signals, timeout=1)
    assert process_ignoring_signals.returncode == -signal.SIGKILL
    output = process_ignoring_signals.stdout.read()
    assert 'Signal ignored.' in output


def test_terminate_gracefully_default_signal(running_process):
    """Check that the default 'gentle' signal sent by ``terminate_gracefully`` is SIGTERM."""
    terminate_gracefully(running_process)
    assert running_process.returncode == -signal.SIGTERM


def test_kill_crudely(running_process):
    """Ensure that ``kill_crudely`` just sends SIGKILL, no matter what."""
    kill_crudely(running_process)
    assert running_process.returncode == -signal.SIGKILL

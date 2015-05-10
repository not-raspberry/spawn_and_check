"""Executor tests."""
import pytest

from mock import Mock, MagicMock

from spawn_and_check import execute
from spawn_and_check.exceptions import PreChecksFailed, PostChecksFailed, SubprocessExited


FAKE_COMMAND = 'never to be called'
"""
This command will fail

It is used as a placeholder for commands that will never be executed because e.g. checks fail.
"""


def test_execute_raises_if_shlex_wold_block():
    """
    Check if execute raises ValueError when None is passed instead of the command.

    That would cause ``shlex.split`` to read from stdin.
    """
    with pytest.raises(ValueError):
        execute(None, [])


@pytest.mark.parametrize('checks_count', range(2, 6))
def test_execute_pre_checks_fail(invalid_check, checks_count):
    """Test if ``execute`` raises ``PreChecksFailed`` if pre-execute checks fail."""
    failing_pre_checks = [lambda: False] * checks_count
    with pytest.raises(PreChecksFailed):
        execute(FAKE_COMMAND, [invalid_check], pre_checks=failing_pre_checks)


def test_execute_pre_checks_defaults(popen_mock):
    """Test if negated post-checks are used as pre-checks by default."""
    with pytest.raises(PreChecksFailed):
        # We expect the failure to come from pre-checks.
        # A negated version of the passed check will be used as a pre-check.
        execute(FAKE_COMMAND, [lambda: True], timeout=0.1, popen=popen_mock)

    assert not popen_mock.called, 'We shouldn\'t be able to run the command after pre-checks failed.'

    # Positive case - the check fn returns False before Popen and True after - just as in the ideal world:
    execute(FAKE_COMMAND, [lambda: popen_mock.called], timeout=0.1, popen=popen_mock)
    assert popen_mock.called


def test_execute_post_checks_fail(popen_mock):
    """Check if ``PostChecksFailed`` is raised when post checks fail."""
    with pytest.raises(PostChecksFailed):
        execute(FAKE_COMMAND, [lambda: False], timeout=0.1, popen=popen_mock)

    with pytest.raises(PostChecksFailed):
        execute(FAKE_COMMAND, [lambda: not popen_mock.called], pre_checks=[lambda: True], timeout=0.1, popen=popen_mock)


def test_execute_popen_called(popen_mock):
    """Check if the ``execute`` function calls ``Popen`` when checks are OK."""
    process = execute(FAKE_COMMAND, [lambda: popen_mock.called], popen=popen_mock)
    assert popen_mock.popen_called
    # This actually checks if the mocked Popen object was returned.
    assert process.poll() is None


def test_execute_raises_when_process_exits():
    """Check if ``SubprocessExited`` is thrown if the process exits."""
    process_mock = Mock()
    process_mock.poll.return_value = 12
    exiting_popen_mock = Mock(return_value=process_mock)

    with pytest.raises(SubprocessExited):
        execute(FAKE_COMMAND, [lambda: exiting_popen_mock.called], popen=exiting_popen_mock)
    assert exiting_popen_mock.popen_called


def test_execute_waits_for_the_post_checks_to_turn_ok(popen_mock):
    """Check if ``execute`` will poll the checks until they resolve OK or timeout occurs."""
    check = MagicMock(side_effect=[False, False, False, True])
    sleep_mock = Mock()
    execute(FAKE_COMMAND, [check], pre_checks=[lambda: True], sleep_fn=sleep_mock, popen=popen_mock)

    assert popen_mock.called
    assert (check.call_count == 4,
            'The check function should return False 3 times as a post-check and once - and the last time - True.')
    assert sleep_mock.call_count == 3, 'Sleeping should take place after each failed check.'

"""Testing fixtures."""
import pytest
from mock import Mock


@pytest.fixture
def process_mock():
    """Mock for the popened process."""
    process_mock = Mock()
    process_mock.poll.return_value = None

    return process_mock


@pytest.fixture
def popen_mock(process_mock):
    """
    Mock the execute function and allow checks to execute accordingly to the executor state.

    The mocked Popen will behave as if the process ran and didn't terminate immediately. That's the correct behaviour
    of the process.
    """
    popen_mock = Mock(return_value=process_mock)
    return popen_mock


@pytest.fixture
def invalid_check():
    """A check that we use as a post check to determine it never gets called."""
    def invalid_check_fn():
        assert False, 'This check should never be called.'

    return invalid_check_fn

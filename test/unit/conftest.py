"""Testing fixtures."""
import pytest
from mock import Mock

RETURN_CODE = 43  # Arbitrary number in the range of standard exit codes.


@pytest.fixture
def popen_mock():
    """
    Mock the execute function and allow checks to execute accordingly to the executor state.

    The mocked Popen will behave as if the process ran and didn't terminate immediately. That's the correct behaviour
    of the process.

    .. warning ::
        Single use per test only. The mock registers the mocked ``subprocess.Popen`` has been called so that
        the check fixtures can return True or False accordingly.
    """
    process_mock = Mock()
    process_mock.poll.return_value = None
    popen_mock = Mock(return_value=process_mock)
    return popen_mock


@pytest.fixture
def invalid_check():
    """A check that we use as a post check to determine it never gets called."""
    def invalid_check_fn():
        assert False, 'This check should never be called.'

    return invalid_check_fn

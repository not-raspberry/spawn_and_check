"""
Testing the executor function along with checks.

It is impossible to test the checks with unit tests because of the race condition this library solves - we cannot
know when e.g. the background TCP listener really started listening. It is also impractical to test them in a unit
way because that would require way too much patching and mocking compared to what the checks do.
"""
import pytest
import port_for

from spawn_and_check import execute, check_tcp, check_http, check_unix
from spawn_and_check.exceptions import PostChecksFailed

SERVICE = './test/fake_service/service.py'
DELAYS = [0, 3, 5]  # Seconds before the service starts serving (lower bound).


def test_execute_failing_checks():
    """Test if failing checks result in ``PostChecksFailed`` being thrown."""
    port = check_tcp(port_for.select_random())
    tcp_check = check_tcp(port)
    unix_check = check_unix('no_such_sock')
    http_check = check_http('http://127.0.0.1:%s' % port)

    processes = []

    with pytest.raises(PostChecksFailed):
        processes.append(execute('sleep 10', [tcp_check], timeout=1))

    with pytest.raises(PostChecksFailed):
        processes.append(execute('sleep 10', [unix_check], timeout=1))

    with pytest.raises(PostChecksFailed):
        processes.append(execute('sleep 10', [http_check], timeout=1))

    with pytest.raises(PostChecksFailed):
        # 3 failing checks at once.
        processes.append(execute('sleep 10', [http_check, unix_check, tcp_check], timeout=1))

    # Clean up the mess the test created.
    for process in processes:
        process.kill()


@pytest.mark.parametrize('delay', DELAYS)
def test_execute_check_tcp(delay):
    """Check the executor with the TCP check."""
    port = port_for.select_random()
    check = check_tcp(port)

    assert check() is False
    process = execute(
        [SERVICE, '--delay', str(delay), 'tcp', '--port', str(port)],
        [check_tcp(port)],
        timeout=1 + delay)
    assert check() is True
    assert process.poll() is None  # Still running.
    process.kill()


@pytest.mark.parametrize('delay', DELAYS)
def test_execute_check_unix(tmpdir, delay):
    """Check the executor with the unix socket check."""
    socket_file = str(tmpdir / 'temp_unix_socket')
    check = check_unix(socket_file)

    assert check() is False
    process = execute(
        [SERVICE, '--delay', str(delay), 'unix', '--socket-file', socket_file],
        [check_unix(socket_file)],
        timeout=1 + delay)
    assert check() is True
    assert process.poll() is None
    process.kill()


@pytest.mark.parametrize('delay', DELAYS)
def test_execute_check_http(delay):
    """Check the executor with the HTTP HEAD request check."""
    port = port_for.select_random()
    good_path = '/good_path'

    check = check_http('http://127.0.0.1:%s%s' % (port, good_path))
    check_bad_path = check_http('http://127.0.0.1:%s/bad_path' % port)  # This request will not return 200.

    assert check() is False
    assert check_bad_path() is False

    process = execute(
        [SERVICE, '--delay', str(delay), 'http', '--port', str(port), '--path', good_path],
        [check],
        timeout=1 + delay)
    assert check() is True
    assert check_bad_path() is False

    assert process.poll() is None
    process.kill()

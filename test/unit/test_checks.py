"""Tests for checks' helpers."""
import pytest
from spawn_and_check.checks import is_response_ok, http_urlsplit


@pytest.mark.parametrize('url, expected_split', [
    ['http://example.com', ('example.com', '80', '')],
    ['http://example.com/', ('example.com', '80', '/')],
    ['http://example.com:4321/', ('example.com', '4321', '/')],
    ['http://example.com:4321/path_path', ('example.com', '4321', '/path_path')],
])
def test_check_http_url_split(url, expected_split):
    """Check if http_urlsplit returns host, port, and path and fills the port number with 80 if not given."""
    assert http_urlsplit(url) == expected_split


def test_check_http_url_split_validation():
    """Check if http_urlsplit validates scheme."""
    with pytest.raises(ValueError):
        http_urlsplit('https://aaa.cz')

    with pytest.raises(ValueError):
        http_urlsplit('ftp://ddd.cz')


def test_is_response_ok():
    """Check if response code in bounds: [200, 300) is treated as OK."""
    assert is_response_ok(100) is False
    assert is_response_ok(200) is True
    assert is_response_ok(250) is True
    assert is_response_ok(299) is True
    assert is_response_ok(300) is False

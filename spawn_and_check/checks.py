"""
Functions returning service checks.

Those functions are effectively partials but we do care about their representation (__name__, __doc__) so we cannot use
``functools.partial``.
"""
import socket
from urlparse import urlsplit
from httplib import HTTPConnection

DEFAULT_TIMEOUT = 1.0  # sec


def check_tcp(port, host='127.0.0.1', timeout=DEFAULT_TIMEOUT):
    """
    Create a TCP check function.

    :param int port:
    :param str host: numeric hostname or a resolvable hostname (IPv4 or IPv6)
    """
    def check_tcp():
        """
        Try to establish a TCP connection.

        The connection will be immediately broken after it is established.

        :rtype: bool
        :return: True if can connect, else False
        """
        try:
            tcp_socket = socket.create_connection((host, port), timeout)
            tcp_socket.close()
            return True
        except socket.error:
            return False

    return check_tcp


def check_unix(path):
    """
    Create a unix socket check function.

    :param str path: path to the socket file
    """
    def check_unix():
        """
        Try to establish a unix socket connection.

        The connection will be immediately broken after it is established.

        :rtype: bool
        :return: True if can connect, else False
        """
        try:
            unix_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            unix_socket.connect(path)
            return True
        except socket.error:
            return False
        finally:
            unix_socket.close()

    return check_unix


def http_urlsplit(url):
    """
    Validate and split the URL into host, port, and path parts.

    :param str url:
    :rtype: tuple
    :return: 3-tuple of strings: host, port and path
    """
    url_parts = urlsplit(url)

    if url_parts.scheme != 'http':
        raise ValueError('The scheme of the URL should be HTTP.')

    try:
        host, port = url_parts.netloc.split(':')
    except ValueError:
        host, port = url_parts.netloc, '80'

    return host, port, url_parts.path


def is_response_ok(code):
    """
    Check if the HTTP response code is in boundaries of an OK response.

    :param int code:
    :rtype bool:
    :return: True if OK, else False
    """
    return 200 <= code < 300


def check_http(url, HTTPConnection=HTTPConnection):
    """
    Create a HTTP HEAD check function.

    :param str url: URL to sent HEAD to
    """
    def check_http():
        """
        Try to send HTTP HEAD request to the address.

        :param str url:
        :rtype: bool
        :return: True if the response was OK (2XX), False otherwise
        """
        host, port, path = http_urlsplit(url)

        connection = HTTPConnection(host, port)
        try:
            connection.request('HEAD', path)
            response = connection.getresponse()
        except socket.error:
            return False

        return is_response_ok(response.status)

    return check_http

#!/usr/bin/env python
"""
Fake services for testing the executor and checks.

We cannot simply test with Popen + netcat because netcat options are not portable even
between modern Linux distributions.

.. warning ::
    Those are not good examples on how to write socket programs. In fact you rather shouldn't
    use sockets directly. The only purpose of the commands below is to be used in tests.
"""
import os
import socket
import signal
import errno
from time import sleep
from threading import Timer
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

import click

HOST = '127.0.0.1'
BUFFER_SIZE = 1024


@click.group()
@click.option('--delay', type=float, default=0.0, help='Number of seconds to sleep before the service is started')
def fake_service(delay):
    """Run a service that performs an action detected by a tested checker or executor."""
    sleep(delay)


@fake_service.command()
@click.option('--log-file', type=click.File(mode='w'), default='-', help='File to log messages to')
@click.option('--message', type=unicode, default='Fake app is running.', help='Message to log when running')
def output(log_file, message):
    """Simply write to a file."""
    log_file.write(message)


def listen_stream(protocol_family, address_to_bind):
    """
    Listen indefinitely on a socket of SOCK_STREAM type and print received bytes.

    :param int protocol_family: one of SOCK_* constants in ``socket`` library
    :param address_to_bind: argument to pass to the bind method of the socket object,
        depending on the socket type (most probably a host and port tuple or a file path)
    """
    stream_socket = socket.socket(protocol_family, socket.SOCK_STREAM)
    stream_socket.bind(address_to_bind)
    stream_socket.listen(0)  # No backlog.

    while True:
        try:
            connection, addr = stream_socket.accept()
            print 'Connection from', addr
            while True:
                received = connection.recv(BUFFER_SIZE)
                if not received:
                    break
                print 'Received: %r' % received

        except socket.error as e:
            if e.errno != errno.EINTR:
                raise


@fake_service.command()
@click.option('--port', type=int, help='TCP port to bind and listen on')
def tcp(port):
    """Listen on a TCP socket."""
    listen_stream(socket.AF_INET, (HOST, port))


@fake_service.command()
@click.option('--socket-file', type=str,
              help='Unix socket to bind and listen on. The file will be created automatically.')
def unix(socket_file):
    """Listen on a unix socket."""
    listen_stream(socket.AF_UNIX, socket_file)


@fake_service.command()
@click.option('--port', type=int, help='UDP port to bind and listen on')
def udp(port):
    """Listen indefinitely on a UDP socket."""
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('0.0.0.0', port))

    while True:
        try:
            received, address = udp_socket.recvfrom(BUFFER_SIZE)
            print 'Received: %r from %r' % (received, address)
        except socket.error as e:
            if e.errno != errno.EINTR:
                raise


class FakeHTTPServer(HTTPServer):

    """HTTP server with information about the accepted path."""

    def __init__(self, *args, **kwargs):
        """
        In addition to the magic done by the super constructor, store the accepted path.

        :param str accepted_path: path of requests that will be responded with OK
        """
        self.accepted_path = kwargs.pop('accepted_path')
        # Old style classes, Yo!
        HTTPServer.__init__(self, *args, **kwargs)


class FakeHTTPRequestHandler(BaseHTTPRequestHandler):

    """HTTP request handler that answers the HEAD requests; for testing only."""

    def do_HEAD(self):
        """Respond with OK if the request path matches, NOT FOUND otherwise."""
        if self.path == self.server.accepted_path:
            self.send_response(200, '')
        else:
            self.send_response(404, '')


@fake_service.command()
@click.option('--port', type=int, help='The port to bind and run test HTTP server on')
@click.option('--path', type=str, default='/', help='URL path to respond with OK for (should begin with a slash)')
def http(port, path):
    """Run a test HTTP server."""
    httpd = FakeHTTPServer((HOST, port), FakeHTTPRequestHandler, accepted_path=path)
    httpd.serve_forever()


def terminate_sloppily(signum, frame):
    """
    Terminate the process but... uhm... give me 2 seconds.

    This is needed for testing the case when the same service is executed just after its
    termination.
    """
    print "SIGTERM trapped but it's not like I'm going to exit now, oh no."

    def do_exit():
        print "OK, I'm exiting."
        os._exit(1)  # Make the whole process exit, not just current thread.

    exit_after_20_sec = Timer(2, do_exit)
    exit_after_20_sec.start()


if __name__ == '__main__':
    print 'Fake service PID:', os.getpid()
    signal.signal(signal.SIGTERM, terminate_sloppily)
    fake_service()

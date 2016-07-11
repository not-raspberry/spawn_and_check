#!/usr/bin/env python
"""A script that ignores SIGTERM and SIGABRT and wastes your time."""
import os
import sys
import signal


def handle_signal_mindlessly(signum, frame):
    """Handle SIGTERM... or don't."""
    print 'Signal ignored. Send something more convincing.'
    sys.stdout.flush()


if __name__ == '__main__':
    print "Idle signal malcontent's PID:", os.getpid()
    signal.signal(signal.SIGTERM, handle_signal_mindlessly)
    signal.signal(signal.SIGABRT, handle_signal_mindlessly)
    print 'Ignoring signals since now!'
    sys.stdout.flush()
    while True:
        signal.pause()

# Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA.


import fcntl
import logging
import re
import socket
import struct
import sys

# from paramiko.py3compat import u

from .common import get_local_terminal_size

# windows does not have termios...
try:
    import termios
    import tty

    has_termios = True
except ImportError:
    has_termios = False

# logger = get_logger(__name__)
logger = logging.getLogger(__name__)


class SessionLogger():

    csi_escape_seq = re.compile(br'\x1b\[(?:[0-?]+)?(?:[ -\/]+)?[@-~]?')
    # backspace_escape = re.compile(br'\w\x08')
    backspace_escape = re.compile(br'\n(.*\r\r)(?!\n)')
    car_return_escape = re.compile(br'\s+\r')

    def __init__(self, filename) -> None:
        self._buffer = bytearray()
        self.filename = filename
        pass

    def write(self, some_bytes, force=False):
        self._buffer.extend(some_bytes)
        if (len(self._buffer) >= 1024) or force:
            with open(self.filename, 'ab') as f:
                self._buffer = self.csi_escape_seq.sub(b'', self._buffer)
                self._buffer = self.backspace_escape.sub(b'\n', self._buffer)
                self._buffer = self.car_return_escape.sub(b'', self._buffer)
                f.write(self._buffer)
                self._buffer = bytearray()


def interactive_shell(chan, session_log_fname):
    if has_termios:
        posix_shell(chan, session_log_fname)
        logger.debug('Using posix shell')
    else:
        windows_shell(chan)


def posix_shell(chan, session_log_fname):
    import select

    oldtty = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        chan.settimeout(0.0)

        if session_log_fname:
            session_logger = SessionLogger(session_log_fname)

        while True:
            if not chan.closed:
                chan.resize_pty(
                    *get_local_terminal_size()
                )
            r, w, e = select.select([chan, sys.stdin], [], [])
            wat = fcntl.ioctl(r[0].fileno(), termios.FIONREAD, "  ")
            doublewat = struct.unpack('h', wat)[0]
            if chan in r:
                try:
                    # x = u(chan.recv(1024))
                    # try:
                    #     # x = u(chan.recv(1024))
                    #     x = chan.recv(1024)
                    #     # TODO implement session logging here
                    #     # logger.debug('Message recieved')
                    #     # logger.debug(x)
                    # except UnicodeDecodeError as err:
                    #     logger.debug(flatten_log_msg(err))
                    # TODO check and review the number (1024)
                    x = chan.recv(1024)

                    if len(x) == 0:
                        sys.stdout.buffer.write(b"\r\n*** EOF\r\n")
                        if session_log_fname:
                            session_logger.write(x, force=True)
                        break
                    sys.stdout.buffer.write(x)
                    if session_log_fname:
                        session_logger.write(x)
                    sys.stdout.buffer.flush()
                except socket.timeout:
                    pass
            if sys.stdin in r:
                x = sys.stdin.read(doublewat)
                if len(x) == 0:
                    if session_log_fname:
                        session_logger.write(b'', force=True)
                    break
                chan.send(x)

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)


# thanks to Mike Looijmans for this code
def windows_shell(chan):
    import threading

    sys.stdout.write(
        "Line-buffered terminal emulation. Press F6 or ^Z to send EOF.\r\n\r\n"
    )

    def writeall(sock):
        while True:
            data = sock.recv(256)
            if not data:
                sys.stdout.write("\r\n*** EOF ***\r\n\r\n")
                sys.stdout.flush()
                break
            sys.stdout.write(data)
            sys.stdout.flush()

    writer = threading.Thread(target=writeall, args=(chan,))
    writer.start()

    try:
        while True:
            d = sys.stdin.read(1)
            if not d:
                break
            chan.send(d)
    except EOFError:
        # user hit ^Z or F6
        pass

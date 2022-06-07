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


from asyncio.log import logger
import socket
import sys
import fcntl
import struct
from paramiko.py3compat import u

from .common import get_local_terminal_size, flatten_log_msg

# windows does not have termios...
try:
    import termios
    import tty

    has_termios = True
except ImportError:
    has_termios = False


def interactive_shell(chan):
    if has_termios:
        posix_shell(chan)
    else:
        windows_shell(chan)


def posix_shell(chan):
    import select

    oldtty = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        chan.settimeout(0.0)

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
                    try:
                        x = u(chan.recv(1024))
                    except UnicodeDecodeError as e:
                        logger.debug(flatten_log_msg(e))
                    # A:i80dcgw1# Traceback (most recent call last):
                    # File "/home/ivan/dev/pysc/pysc/./pysc.py", line 12, in <module>
                    #     main()
                    # File "/home/ivan/dev/pysc/pysc/./pysc.py", line 9, in main
                    #     commands.connect(sys.argv[2])
                    # File "/home/ivan/dev/pysc/pysc/commands.py", line 4, in connect
                    #     SSHConnection(target_host).connect()
                    # File "/home/ivan/dev/pysc/pysc/connection.py", line 127, in connect
                    #     interactive.interactive_shell(channel)
                    # File "/home/ivan/dev/pysc/pysc/interactive.py", line 46, in interactive_shell
                    #     posix_shell(chan)
                    # File "/home/ivan/dev/pysc/pysc/interactive.py", line 96, in posix_shell
                    #     x = u(chan.recv(1024))
                    # File "/home/ivan/.local/lib/python3.10/site-packages/paramiko/py3compat.py", line 161, in u
                    #     return s.decode(encoding)
                    # UnicodeDecodeError: 'utf-8' codec can't decode byte 0xd0 in position 0: unexpected end of data
                    # TODO
                    
                    if len(x) == 0:
                        sys.stdout.write("\r\n*** EOF\r\n")
                        break
                    sys.stdout.write(x)
                    sys.stdout.flush()
                except socket.timeout:
                    pass
            if sys.stdin in r:
                x = sys.stdin.read(doublewat)
                if len(x) == 0:
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
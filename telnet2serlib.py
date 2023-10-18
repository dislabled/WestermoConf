#!/usr/bin/env python3
# -*- coding=utf-8 -*-
"""Library to make a telnet to serial shim."""

import sys
import logging
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from select import select
from serial import Serial, SerialException  # type: ignore

# logging config:
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


def cleanup_for_serial(text):
    """Replace some characters for cleanup."""
    # chr(255) is the "we are negotiating" leading bit.  If it is the first bit in
    # a packet, we do not want to send it on to the serial port
    if ord(text[:1]) == 255:
        return ""

    # For some reason, windows likes to send "cr/lf" when you send a "cr".
    # Strip that so we don't get a double prompt.\
    text = text.decode("latin-1")
    text = text.replace(chr(13) + chr(10), chr(13))
    text = text.encode("latin-1")

    return text


class ProtocolInteractions:
    """Class to forward requests between TCP and Serial."""

    def __init__(self, sock, com) -> None:
        """Initialize the class."""
        self.sock = sock
        self.com = com

    def fileno(self) -> socket:
        """Get fileno of socket."""
        return self.sock.fileno()

    def recv_tcp(self) -> str:
        """Receive some data from the telnet client."""
        data = self.sock.recv(1024)
        return data

    def send_tcp(self, data) -> None:
        """Send some data out to the telnet client."""
        self.sock.send(data)

    def recv_serial(self) -> str:
        """Receive some data from the serial port."""
        data = self.com.read(self.com.inWaiting())
        return data

    def send_serial(self, data) -> None:
        """Send some data out to the serial port."""
        data = cleanup_for_serial(data)
        try:
            self.com.write(data)
        except TypeError:
            self.com.write(data.encode("latin-1"))


class Handler:
    """Class to start the handler."""

    def __init__(
        self,
        tel_port: int = 2323,
        ser_port: str = "/dev/ttyUSB0",
        baud: int = 115200,
        timeout: int = 1,
        xonxoff: bool = True,
    ) -> None:
        """Initialize the class."""
        self.tel_port = tel_port
        self.com = Serial(
            port=ser_port, baudrate=baud, timeout=timeout, xonxoff=xonxoff
        )
        self.clist: list = []
        self.start_new_listener()

    def start_new_listener(self) -> None:
        """Start the telnet listener."""
        logger.debug("Starting the telnet listener")
        self.listener: socket | None = socket(AF_INET, SOCK_STREAM)
        self.listener.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.listener.bind(("", self.tel_port))
        self.listener.listen(32)

    def run(self) -> None:
        """Check for incoming telnet connections and start interactions."""
        for tcp_conn in self.clist[:]:
            if tcp_conn.com.isOpen():
                # pull data from serial and send it to tcp if possible
                data = tcp_conn.recv_serial()
                if data:
                    tcp_conn.send_tcp(data)

        ready = self.clist[:]

        if self.listener:
            ready.append(self.listener)

        ready = select(ready, [], [], 0.1)[0]
        for tcp_conn in ready:
            if tcp_conn is self.listener:
                if self.listener is not None:
                    sock, address = self.listener.accept()
                    logger.debug("Telnet connection from %s", address)
                    try:
                        self.com.close()
                        self.com.open()
                    except SerialException:
                        logger.critical("Error opening serial port.")
                        sys.exit(1)

                    tcp_conn = ProtocolInteractions(sock, self.com)
                    self.clist.append(tcp_conn)

                    # stop the listener when we have a connection
                    self.listener = None
            else:
                # try to pull from tcp and send to serial
                data = tcp_conn.recv_tcp()
                if not data:
                    logger.warning("TCP connection closed.")
                    # self.clist.remove(tcp_conn)
                    quit()
                    # self.start_new_listener()

                else:
                    tcp_conn.send_serial(data)


if __name__ == "__main__":
    try:
        connections = Handler()
        while True:
            connections.run()
    except KeyboardInterrupt:
        print("Keyboard Interrupt")

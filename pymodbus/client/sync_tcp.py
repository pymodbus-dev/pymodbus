"""**Modbus client TCP communication.**

Example::

    from pymodbus.client import ModbusTcpClient

    def run():
        client = ModbusTcpClient(
            "127.0.0.1",
            #    port=502,  # on which port
            # Common optional paramers:
            #    modbus_decoder=ClientDecoder,
            #    framer=ModbusSocketFramer,  # how to interpret the messages
            #    timeout=10,  # waiting time for request to complete
            #    retries=3,  # retries per transaction
            #    retry_on_empty=False,  # Is an empty response a retry
            #    close_comm_on_error=False,  # close connection when error.
            #    strict=True,  # use strict timing, t1.5 for Modbus RTU
            # TCP setup parameters
            #    source_address=("localhost", 0),  # bind socket to address
        )

        client.start()
        ...
        client.stop()
"""
import logging
import select
import socket
import time

from pymodbus.exceptions import ConnectionException
from pymodbus.utilities import ModbusTransactionState
from pymodbus.client.base import ModbusBaseClient
from pymodbus.transaction import ModbusSocketFramer

_logger = logging.getLogger(__name__)


class ModbusTcpClient(ModbusBaseClient):
    r"""Modbus client for TCP communication.

    :param host: (positional) Host IP address
    :param port: (optional default 502) The TCP port used for communication.
    :param modbus_decoder: (optional, default ClientDecoder) Message decoder class.
    :param framer: (optional, default ModbusSocketFramer) Framer class.
    :param source_address: (optional, default none) source address of client,
    :param \*\*kwargs: (optional) Extra experimental parameters for transport
    :return: client object
    """

    def __init__(
        self,
        host,
        port=502,
        framer=ModbusSocketFramer,
        source_address=None,
        **kwargs,
    ):
        """Initialize Modbus TCP Client."""
        self.host = host
        self.port = port
        self.source_address = source_address
        super().__init__(framer=framer, **kwargs)
        self.socket = None

    def start(self):
        """Connect to the modbus tcp server.

        :returns: True if connection succeeded, False otherwise
        """
        if self.socket:
            return True
        try:
            self.socket = socket.create_connection(
                (self.host, self.port),
                timeout=self.timeout,
                source_address=self.source_address,
            )
            txt = f"Connection to Modbus server established. Socket {self.socket.getsockname()}"
            _logger.debug(txt)
        except socket.error as msg:
            txt = f"Connection to ({self.host}, {self.port}) failed: {msg}"
            _logger.error(txt)
            self.close()
        return self.socket is not None

    def close(self):
        """Close the underlying socket connection."""
        if self.socket:
            self.socket.close()
        self.socket = None

    def _check_read_buffer(self):
        """Check read buffer."""
        time_ = time.time()
        end = time_ + self.timeout
        data = None
        ready = select.select([self.socket], [], [], end - time_)
        if ready[0]:
            data = self.socket.recv(1024)
        return data

    def _send(self, request):  # pylint: disable=missing-type-doc
        """Send data on the underlying socket.

        :param request: The encoded request to send
        :return: The number of bytes written
        :raises ConnectionException:
        """
        if not self.socket:
            raise ConnectionException(str(self))
        if self.state == ModbusTransactionState.RETRYING:
            if data := self._check_read_buffer():
                return data

        if request:
            return self.socket.send(request)
        return 0

    def _recv(self, size):  # pylint: disable=missing-type-doc
        """Read data from the underlying descriptor.

        :param size: The number of bytes to read
        :return: The bytes read if the peer sent a response, or a zero-length
                 response if no data packets were received from the client at
                 all.
        :raises ConnectionException:
        """
        if not self.socket:
            raise ConnectionException(str(self))

        # socket.recv(size) waits until it gets some data from the host but
        # not necessarily the entire response that can be fragmented in
        # many packets.
        # To avoid split responses to be recognized as invalid
        # messages and to be discarded, loops socket.recv until full data
        # is received or timeout is expired.
        # If timeout expires returns the read data, also if its length is
        # less than the expected size.
        self.socket.setblocking(0)

        timeout = self.timeout

        # If size isn"t specified read up to 4096 bytes at a time.
        if size is None:
            recv_size = 4096
        else:
            recv_size = size

        data = []
        data_length = 0
        time_ = time.time()
        end = time_ + timeout
        while recv_size > 0:
            try:
                ready = select.select([self.socket], [], [], end - time_)
            except ValueError:
                return self._handle_abrupt_socket_close(size, data, time.time() - time_)
            if ready[0]:
                if (recv_data := self.socket.recv(recv_size)) == b"":
                    return self._handle_abrupt_socket_close(
                        size, data, time.time() - time_
                    )
                data.append(recv_data)
                data_length += len(recv_data)
            time_ = time.time()

            # If size isn"t specified continue to read until timeout expires.
            if size:
                recv_size = size - data_length

            # Timeout is reduced also if some data has been received in order
            # to avoid infinite loops when there isn"t an expected response
            # size and the slave sends noisy data continuously.
            if time_ > end:
                break

        return b"".join(data)

    def _handle_abrupt_socket_close(self, size, data, duration):  # pylint: disable=missing-type-doc
        """Handle unexpected socket close by remote end.

        Intended to be invoked after determining that the remote end
        has unexpectedly closed the connection, to clean up and handle
        the situation appropriately.

        :param size: The number of bytes that was attempted to read
        :param data: The actual data returned
        :param duration: Duration from the read was first attempted
               until it was determined that the remote closed the
               socket
        :return: The more than zero bytes read from the remote end
        :raises ConnectionException: If the remote end didn't send any
                 data at all before closing the connection.
        """
        self.close()
        size_txt = size if size else "unbounded read"
        readsize = f"read of {size_txt} bytes"
        msg = (
            f"{self}: Connection unexpectedly closed "
            f"{duration} seconds into {readsize}"
        )
        if data:
            result = b"".join(data)
            msg += f" after returning {len(result)} bytes"
            _logger.warning(msg)
            return result
        msg += " without response from unit before it closed connection"
        raise ConnectionException(msg)

    def is_socket_open(self):
        """Check if socket is open."""
        return self.socket is not None

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return f"ModbusTcpClient({self.host}:{self.port})"

    def __repr__(self):
        """Return string representation."""
        return (
            f"<{self.__class__.__name__} at {hex(id(self))} socket={self.socket}, "
            f"ipaddr={self.host}, port={self.port}, timeout={self.timeout}>"
        )

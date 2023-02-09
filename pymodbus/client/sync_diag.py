"""Sync diag."""
import socket
import time

from pymodbus.client.tcp import ModbusTcpClient
from pymodbus.constants import Defaults
from pymodbus.exceptions import ConnectionException
from pymodbus.framer.socket_framer import ModbusSocketFramer
from pymodbus.logging import Log


LOG_MSGS = {
    "conn_msg": "Connecting to modbus device %s",
    "connfail_msg": "Connection to (%s, %s) failed: %s",
    "discon_msg": "Disconnecting from modbus device %s",
    "timelimit_read_msg": "Modbus device read took %.4f seconds, "
    "returned %s bytes in timelimit read",
    "timeout_msg": "Modbus device timeout after %.4f seconds, returned %s bytes %s",
    "delay_msg": "Modbus device read took %.4f seconds, "
    "returned %s bytes of %s expected",
    "read_msg": "Modbus device read took %.4f seconds, "
    "returned %s bytes of %s expected",
    "unexpected_dc_msg": "%s %s",
}


class ModbusTcpDiagClient(ModbusTcpClient):
    """Variant of pymodbus.client.ModbusTcpClient.

    With additional logging to diagnose network issues.

    The following events are logged:

    +---------+-----------------------------------------------------------------+
    | Level   | Events                                                          |
    +=========+=================================================================+
    | ERROR   | Failure to connect to modbus unit; unexpected disconnect by     |
    |         | modbus unit                                                     |
    +---------+-----------------------------------------------------------------+
    | WARNING | Timeout on normal read; read took longer than warn_delay_limit  |
    +---------+-----------------------------------------------------------------+
    | INFO    | Connection attempt to modbus unit; disconnection from modbus    |
    |         | unit; each time limited read                                    |
    +---------+-----------------------------------------------------------------+
    | DEBUG   | Normal read with timing information                             |
    +---------+-----------------------------------------------------------------+

    Reads are differentiated between "normal", which reads a specified number of
    bytes, and "time limited", which reads all data for a duration equal to the
    timeout period configured for this instance.
    """

    def __init__(
        self,
        host="127.0.0.1",
        port=Defaults.TcpPort,
        framer=ModbusSocketFramer,
        **kwargs,
    ):
        """Initialize a client instance.

        The keys of LOG_MSGS can be used in kwargs to customize the messages.

        :param host: The host to connect to (default 127.0.0.1)
        :param port: The modbus port to connect to (default 502)
        :param source_address: The source address tuple to bind to (default ("", 0))
        :param timeout: The timeout to use for this socket (default Defaults.Timeout)
        :param warn_delay_limit: Log reads that take longer than this as warning.
               Default True sets it to half of "timeout". None never logs these as
               warning, 0 logs everything as warning.
        :param framer: The modbus framer to use (default ModbusSocketFramer)

        .. note:: The host argument will accept ipv4 and ipv6 hosts
        """
        self.warn_delay_limit = kwargs.get("warn_delay_limit", True)
        super().__init__(host, port, framer, **kwargs)
        if self.warn_delay_limit is True:
            self.warn_delay_limit = self.params.timeout / 2

        # Set logging messages, defaulting to LOG_MSGS
        for (k_item, v_item) in LOG_MSGS.items():
            self.__dict__[k_item] = kwargs.get(k_item, v_item)

    def connect(self):
        """Connect to the modbus tcp server.

        :returns: True if connection succeeded, False otherwise
        """
        if self.socket:
            return True
        try:
            Log.info(LOG_MSGS["conn_msg"], self)
            self.socket = socket.create_connection(
                (self.params.host, self.params.port),
                timeout=self.params.timeout,
                source_address=self.params.source_address,
            )
        except socket.error as msg:
            Log.error(LOG_MSGS["connfail_msg"], self.params.host, self.params.port, msg)
            self.close()
        return self.socket is not None

    def close(self):
        """Close the underlying socket connection."""
        if self.socket:
            Log.info(LOG_MSGS["discon_msg"], self)
            self.socket.close()
        self.socket = None

    def recv(self, size):
        """Receive data."""
        try:
            start = time.time()

            result = super().recv(size)

            delay = time.time() - start
            if self.warn_delay_limit is not None and delay >= self.warn_delay_limit:
                self._log_delayed_response(len(result), size, delay)
            elif not size:
                Log.debug(LOG_MSGS["timelimit_read_msg"], delay, len(result))
            else:
                Log.debug(LOG_MSGS["read_msg"], delay, len(result), size)

            return result
        except ConnectionException as exc:
            # Only log actual network errors, "if not self.socket" then it's a internal code issue
            if "Connection unexpectedly closed" in exc.string:
                Log.error(LOG_MSGS["unexpected_dc_msg"], self, exc)
            raise ConnectionException from exc

    def _log_delayed_response(self, result_len, size, delay):
        """Log delayed response."""
        if not size and result_len > 0:
            Log.info(LOG_MSGS["timelimit_read_msg"], delay, result_len)
        elif (
            (not result_len) or (size and result_len < size)
        ) and delay >= self.params.timeout:
            size_txt = size if size else "in timelimit read"
            read_type = f"of {size_txt} expected"
            Log.warning(LOG_MSGS["timeout_msg"], delay, result_len, read_type)
        else:
            Log.warning(LOG_MSGS["delay_msg"], delay, result_len, size)

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return f"ModbusTcpDiagClient({self.params.host}:{self.params.port})"


def get_client():
    """Return an appropriate client based on logging level.

    This will be ModbusTcpDiagClient by default, or the parent class
    if the log level is such that the diagnostic client will not log
    anything.

    :returns: ModbusTcpClient or a child class thereof
    """
    return ModbusTcpDiagClient


# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #

__all__ = ["ModbusTcpDiagClient", "get_client"]

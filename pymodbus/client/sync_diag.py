import socket
import logging
import time

from pymodbus.constants import Defaults
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.exceptions import ConnectionException

_logger = logging.getLogger(__name__)

LOG_MSGS = {
    'conn_msg': 'Connecting to modbus device %s',
    'connfail_msg': 'Connection to (%s, %s) failed: %s',
    'discon_msg': 'Disconnecting from modbus device %s',
    'timelimit_read_msg':
        'Modbus device read took %.4f seconds, '
        'returned %s bytes in timelimit read',
    'timeout_msg':
        'Modbus device timeout after %.4f seconds, '
        'returned %s bytes %s',
    'delay_msg':
        'Modbus device read took %.4f seconds, '
        'returned %s bytes of %s expected',
    'read_msg':
        'Modbus device read took %.4f seconds, '
        'returned %s bytes of %s expected',
    'unexpected_dc_msg': '%s %s'}


class ModbusTcpDiagClient(ModbusTcpClient):
    """
    Variant of pymodbus.client.sync.ModbusTcpClient with additional
    logging to diagnose network issues.

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

    # pylint: disable=no-member

    def __init__(self, host='127.0.0.1', port=Defaults.Port,
                 framer=ModbusSocketFramer, **kwargs):
        """ Initialize a client instance

        The keys of LOG_MSGS can be used in kwargs to customize the messages.

        :param host: The host to connect to (default 127.0.0.1)
        :param port: The modbus port to connect to (default 502)
        :param source_address: The source address tuple to bind to (default ('', 0))
        :param timeout: The timeout to use for this socket (default Defaults.Timeout)
        :param warn_delay_limit: Log reads that take longer than this as warning.
               Default True sets it to half of "timeout". None never logs these as
               warning, 0 logs everything as warning.
        :param framer: The modbus framer to use (default ModbusSocketFramer)

        .. note:: The host argument will accept ipv4 and ipv6 hosts
        """
        self.warn_delay_limit = kwargs.get('warn_delay_limit', True)
        super(ModbusTcpDiagClient, self).__init__(host, port, framer, **kwargs)
        if self.warn_delay_limit is True:
            self.warn_delay_limit = self.timeout / 2

        # Set logging messages, defaulting to LOG_MSGS
        for (k, v) in LOG_MSGS.items():
            self.__dict__[k] = kwargs.get(k, v)

    def connect(self):
        """ Connect to the modbus tcp server

        :returns: True if connection succeeded, False otherwise
        """
        if self.socket:
            return True
        try:
            _logger.info(self.conn_msg, self)
            self.socket = socket.create_connection(
                (self.host, self.port),
                timeout=self.timeout,
                source_address=self.source_address)
        except socket.error as msg:
            _logger.error(self.connfail_msg, self.host, self.port, msg)
            self.close()
        return self.socket is not None

    def close(self):
        """ Closes the underlying socket connection
        """
        if self.socket:
            _logger.info(self.discon_msg, self)
            self.socket.close()
        self.socket = None

    def _recv(self, size):
        try:
            start = time.time()

            result = super(ModbusTcpDiagClient, self)._recv(size)

            delay = time.time() - start
            if self.warn_delay_limit is not None and delay >= self.warn_delay_limit:
                self._log_delayed_response(len(result), size, delay)
            elif not size:
                _logger.debug(self.timelimit_read_msg, delay, len(result))
            else:
                _logger.debug(self.read_msg, delay, len(result), size)

            return result
        except ConnectionException as ex:
            # Only log actual network errors, "if not self.socket" then it's a internal code issue
            if 'Connection unexpectedly closed' in ex.string:
                _logger.error(self.unexpected_dc_msg, self, ex)
            raise ex

    def _log_delayed_response(self, result_len, size, delay):
        if not size and result_len > 0:
            _logger.info(self.timelimit_read_msg, delay, result_len)
        elif (result_len == 0 or (size and result_len < size)) and delay >= self.timeout:
            read_type = ("of %i expected" % size) if size else "in timelimit read"
            _logger.warning(self.timeout_msg, delay, result_len, read_type)
        else:
            _logger.warning(self.delay_msg, delay, result_len, size)

    def __str__(self):
        """ Builds a string representation of the connection

        :returns: The string representation
        """
        return "ModbusTcpDiagClient(%s:%s)" % (self.host, self.port)


def get_client():
    """ Returns an appropriate client based on logging level

    This will be ModbusTcpDiagClient by default, or the parent class
    if the log level is such that the diagnostic client will not log
    anything.

    :returns: ModbusTcpClient or a child class thereof
    """
    return ModbusTcpDiagClient if _logger.isEnabledFor(logging.ERROR) else ModbusTcpClient


# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #

__all__ = [
    "ModbusTcpDiagClient", "get_client"
]

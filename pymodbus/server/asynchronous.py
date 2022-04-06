"""
Implementation of a Twisted Modbus Server
------------------------------------------

"""
import logging
import threading
from binascii import b2a_hex
from twisted.internet import protocol
from twisted.internet.protocol import ServerFactory
from twisted.internet import reactor # pylint: disable=unused-import

from pymodbus.constants import Defaults
from pymodbus.utilities import hexlify_packets
from pymodbus.factory import ServerDecoder
from pymodbus.datastore import ModbusServerContext
from pymodbus.device import ModbusControlBlock
from pymodbus.device import ModbusAccessControl
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.exceptions import NoSuchSlaveException
from pymodbus.transaction import ModbusSocketFramer,ModbusAsciiFramer
from pymodbus.pdu import ModbusExceptions as merror

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
_logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Modbus TCP Server
# --------------------------------------------------------------------------- #
class ModbusTcpProtocol(protocol.Protocol):
    """ Implements a modbus server in twisted """

    def __init__(self):
        """Define local variables."""
        self.framer = None

    def connectionMade(self):
        """ Callback for when a client connects

        ..note:: since the protocol factory cannot be accessed from the
                 protocol __init__, the client connection made is essentially
                 our __init__ method.
        """
        txt = f"Client Connected [{self.transport.getHost()}]"
        _logger.debug(txt)
        self.framer = self.factory.framer(decoder=self.factory.decoder,
                                          client=None)

    def connectionLost(self, reason): # pylint: disable=signature-differs
        """ Callback for when a client disconnects

        :param reason: The client's reason for disconnecting
        """
        txt = f"Client Disconnected: {reason}"
        _logger.debug(txt)

    def dataReceived(self, data):
        """ Callback when we receive any data

        :param data: The data sent by the client
        """
        if _logger.isEnabledFor(logging.DEBUG):
            txt = f"Data Received: {hexlify_packets(data)}"
            _logger.debug(txt)
        if not self.factory.control.ListenOnly:
            units = self.factory.store.slaves()
            single = self.factory.store.single
            self.framer.processIncomingPacket(data, self._execute,
                                              single=single,
                                              unit=units)

    def _execute(self, request):
        """ Executes the request and returns the result

        :param request: The decoded request message
        """
        try:
            context = self.factory.store[request.unit_id]
            response = request.execute(context)
        except NoSuchSlaveException:
            txt = f"requested slave does not exist: {request.unit_id}"
            _logger.debug(txt)
            if self.factory.ignore_missing_slaves:
                return # the client will simply timeout waiting for a response
            response = request.doException(merror.GatewayNoResponse)
        except Exception as exc: # pylint: disable=broad-except
            txt = f"Datastore unable to fulfill request: {exc}"
            _logger.debug(txt)
            response = request.doException(merror.SlaveFailure)

        response.transaction_id = request.transaction_id
        response.unit_id = request.unit_id
        self._send(response)

    def _send(self, message):
        """ Send a request (string) to the network

        :param message: The unencoded modbus response
        """
        if message.should_respond:
            self.factory.control.Counter.BusMessage += 1
            pdu = self.framer.buildPacket(message)
            if _logger.isEnabledFor(logging.DEBUG):
                txt = f"send: {b2a_hex(pdu)}"
                _logger.debug(txt)
            return self.transport.write(pdu)
        return None


class ModbusServerFactory(ServerFactory):
    """
    Builder class for a modbus server

    This also holds the server datastore so that it is
    persisted between connections
    """

    protocol = ModbusTcpProtocol

    def __init__(self, store, framer=None, identity=None, **kwargs):
        """ Overloaded initializer for the modbus factory

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param store: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure
        :param ignore_missing_slaves: True to not send errors on a request to a missing slave
        """
        self.decoder = ServerDecoder()
        self.framer = framer or ModbusSocketFramer
        self.store = store or ModbusServerContext()
        self.control = ModbusControlBlock()
        self.access = ModbusAccessControl()
        self.ignore_missing_slaves = kwargs.get('ignore_missing_slaves',
                                                Defaults.IgnoreMissingSlaves)

        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)


# --------------------------------------------------------------------------- #
# Modbus UDP Server
# --------------------------------------------------------------------------- #
class ModbusUdpProtocol(protocol.DatagramProtocol):
    """ Implements a modbus udp server in twisted """

    def __init__(self, store, framer=None, identity=None, **kwargs):
        """ Overloaded initializer for the modbus factory

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param store: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure
        :param ignore_missing_slaves: True to not send errors on a request to
        a missing slave
        """
        framer = framer or ModbusSocketFramer
        self.decoder = ServerDecoder()
        self.framer = framer(self.decoder)
        self.store = store or ModbusServerContext()
        self.control = ModbusControlBlock()
        self.access = ModbusAccessControl()
        self.ignore_missing_slaves = kwargs.get('ignore_missing_slaves',
                                                Defaults.IgnoreMissingSlaves)

        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

    def datagramReceived(self, datagram, addr):
        """ Callback when we receive any data

        :param data: The data sent by the client
        """
        txt = f"Client Connected [{addr}]"
        _logger.debug(txt)
        if _logger.isEnabledFor(logging.DEBUG):
            txt = f"Datagram Received: {hexlify_packets(datagram)}"
            _logger.debug(txt)
        if not self.control.ListenOnly:
            continuation = lambda request: self._execute(request, addr)
            self.framer.processIncomingPacket(datagram, continuation)

    def _execute(self, request, addr):
        """ Executes the request and returns the result

        :param request: The decoded request message
        """
        try:
            context = self.store[request.unit_id]
            response = request.execute(context)
        except NoSuchSlaveException:
            txt = f"requested slave does not exist: {request.unit_id}"
            _logger.debug(txt)
            if self.ignore_missing_slaves:
                return # the client will simply timeout waiting for a response
            response = request.doException(merror.GatewayNoResponse)
        except Exception as exc: # pylint: disable=broad-except
            txt = f"Datastore unable to fulfill request: {exc}"
            _logger.debug(txt)
            response = request.doException(merror.SlaveFailure)
        #self.framer.populateResult(response)
        response.transaction_id = request.transaction_id
        response.unit_id = request.unit_id
        self._send(response, addr)

    def _send(self, message, addr):
        """ Send a request (string) to the network

        :param message: The unencoded modbus response
        :param addr: The (host, port) to send the message to
        """
        self.control.Counter.BusMessage += 1
        pdu = self.framer.buildPacket(message)
        if _logger.isEnabledFor(logging.DEBUG):
            txt = f"send: {b2a_hex(pdu)}"
            _logger.debug(txt)
        return self.transport.write(pdu, addr)


# --------------------------------------------------------------------------- #
# Starting Factories
# --------------------------------------------------------------------------- #
def _is_main_thread():
    if threading.current_thread() != threading.main_thread():
        _logger.debug("Running in spawned thread")
        return False
    _logger.debug("Running in Main thread")
    return True


def StartTcpServer(context, identity=None, address=None, #NOSONAR pylint: disable=dangerous-default-value,invalid-name,too-many-arguments
                   console=False, defer_reactor_run=False, custom_functions=[], #NOSONAR pylint: disable=,unused-argument
                   **kwargs):
    """
    Helper method to start the Modbus Async TCP server

    :param context: The server data context
    :param identify: The server identity to use (default empty)
    :param address: An optional (interface, port) to bind to.
    :param console: A flag indicating if you want the debug console
    :param ignore_missing_slaves: True to not send errors on a request \
    to a missing slave
    :param defer_reactor_run: True/False defer running reactor.run() as part \
    of starting server, to be explictly started by the user
    :param custom_functions: An optional list of custom function classes
        supported by server instance.
    """
    from twisted.internet import reactor as local_reactor # pylint: disable=import-outside-toplevel,reimported

    address = address or ("", Defaults.Port)
    framer = kwargs.pop("framer", ModbusSocketFramer)
    factory = ModbusServerFactory(context, framer, identity, **kwargs)
    for f in custom_functions:
        factory.decoder.register(f)

    txt = f"Starting Modbus TCP Server on {address}"
    _logger.info(txt)
    local_reactor.listenTCP(address[1], factory, interface=address[0]) # pylint: disable=no-member
    if not defer_reactor_run:
        local_reactor.run(installSignalHandlers=_is_main_thread()) # pylint: disable=no-member


def StartUdpServer(context, identity=None, address=None, #NOSONAR pylint: disable=invalid-name,dangerous-default-value
                   defer_reactor_run=False, custom_functions=[], **kwargs):
    """
    Helper method to start the Modbus Async Udp server

    :param context: The server data context
    :param identify: The server identity to use (default empty)
    :param address: An optional (interface, port) to bind to.
    :param ignore_missing_slaves: True to not send errors on a request \
    to a missing slave
    :param defer_reactor_run: True/False defer running reactor.run() as part \
    of starting server, to be explictly started by the user
    :param custom_functions: An optional list of custom function classes
        supported by server instance.
    """
    from twisted.internet import reactor as local_reactor # pylint: disable=import-outside-toplevel,reimported

    address = address or ("", Defaults.Port)
    framer = kwargs.pop("framer", ModbusSocketFramer)
    server = ModbusUdpProtocol(context, framer, identity, **kwargs)
    for f in custom_functions:
        server.decoder.register(f)

    txt = f"Starting Modbus UDP Server on {address}"
    _logger.info(txt)
    local_reactor.listenUDP(address[1], server, interface=address[0])  # pylint: disable=no-member
    if not defer_reactor_run:
        local_reactor.run(installSignalHandlers=_is_main_thread()) # pylint: disable=no-member


def StartSerialServer(context, identity=None, framer=ModbusAsciiFramer, #NOSONAR pylint: disable=invalid-name,dangerous-default-value,too-many-locals
                      defer_reactor_run=False, custom_functions=[], **kwargs):
    """
    Helper method to start the Modbus Async Serial server

    :param context: The server data context
    :param identify: The server identity to use (default empty)
    :param framer: The framer to use (default ModbusAsciiFramer)
    :param port: The serial port to attach to
    :param baudrate: The baud rate to use for the serial device
    :param console: A flag indicating if you want the debug console
    :param ignore_missing_slaves: True to not send errors on a request to a
           missing slave
    :param defer_reactor_run: True/False defer running reactor.run() as part
           of starting server, to be explictly started by the user
    :param custom_functions: An optional list of custom function classes
        supported by server instance.

    """
    from twisted.internet import reactor as local_reactor # pylint: disable=import-outside-toplevel,reimported
    from twisted.internet.serialport import SerialPort # pylint: disable=import-outside-toplevel

    port = kwargs.get('port', '/dev/ttyS0')
    baudrate = kwargs.get('baudrate', Defaults.Baudrate)
    bytesize = kwargs.get("bytesize", Defaults.Bytesize)
    stopbits = kwargs.get("stopbits", Defaults.Stopbits)
    parity = kwargs.get("parity", Defaults.Parity)
    timeout = kwargs.get("timeout", 0)
    xonxoff = kwargs.get("xonxoff", 0)
    rtscts = kwargs.get("rtscts", 0)

    txt = f"Starting Modbus Serial Server on {port}"
    _logger.info(txt)
    factory = ModbusServerFactory(context, framer, identity, **kwargs)
    for f in custom_functions:
        factory.decoder.register(f)

    local_protocol = factory.buildProtocol(None)
    SerialPort.getHost = lambda self: port  # hack for logging
    SerialPort(local_protocol, port, local_reactor, baudrate=baudrate, parity=parity, # pylint: disable=unexpected-keyword-arg
               stopbits=stopbits, timeout=timeout, xonxoff=xonxoff,
               rtscts=rtscts, bytesize=bytesize)
    if not defer_reactor_run:
        local_reactor.run(installSignalHandlers=_is_main_thread()) # pylint: disable=no-member


def StopServer(): #NOSONAR pylint: disable=invalid-name
    """
    Helper method to stop Async Server
    """
    from twisted.internet import reactor as local_reactor # pylint: disable=import-outside-toplevel,reimported
    if _is_main_thread():
        local_reactor.stop()
        _logger.debug("Stopping server from main thread")
    else:
        local_reactor.callFromThread(local_reactor.stop) # pylint: disable=no-member
        _logger.debug("Stopping Server from another thread")


# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #
__all__ = [
    "StartTcpServer", "StartUdpServer", "StartSerialServer", "StopServer"
]

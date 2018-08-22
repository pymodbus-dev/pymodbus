'''
Implementation of a Twisted Modbus Server
------------------------------------------

'''
from binascii import b2a_hex
from twisted.internet import protocol
from twisted.internet.protocol import ServerFactory

from pymodbus.constants import Defaults
from pymodbus.factory import ServerDecoder
from pymodbus.datastore import ModbusServerContext
from pymodbus.device import ModbusControlBlock
from pymodbus.device import ModbusAccessControl
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.exceptions import NoSuchSlaveException
from pymodbus.transaction import ModbusSocketFramer, ModbusAsciiFramer
from pymodbus.pdu import ModbusExceptions as merror
from pymodbus.internal.ptwisted import InstallManagementConsole
from pymodbus.compat import byte2int, IS_PYTHON3
from twisted.internet import reactor

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
_logger = logging.getLogger(__name__)


#---------------------------------------------------------------------------#
# Modbus TCP Server
#---------------------------------------------------------------------------#
class ModbusTcpProtocol(protocol.Protocol):
    ''' Implements a modbus server in twisted '''

    def connectionMade(self):
        ''' Callback for when a client connects

        ..note:: since the protocol factory cannot be accessed from the
                 protocol __init__, the client connection made is essentially
                 our __init__ method.
        '''
        _logger.debug("Client Connected [%s]" % self.transport.getHost())
        self.framer = self.factory.framer(decoder=self.factory.decoder)

    def connectionLost(self, reason):
        ''' Callback for when a client disconnects

        :param reason: The client's reason for disconnecting
        '''
        _logger.debug("Client Disconnected: %s" % reason)

    def dataReceived(self, data):
        ''' Callback when we receive any data

        :param data: The data sent by the client
        '''
        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug(' '.join([hex(byte2int(x)) for x in data]))
        if not self.factory.control.ListenOnly:
            unit_address = byte2int(data[0])
            if unit_address in self.factory.store:
                self.framer.processIncomingPacket(data, self._execute)

    def _execute(self, request, **kwargs):
        ''' Executes the request and returns the result

        :param request: The decoded request message
        '''
        try:
            context = self.factory.store[request.unit_id]
            response = request.execute(context)
        except NoSuchSlaveException as ex:
            _logger.debug("requested slave does not exist: %s" % request.unit_id )
            if self.factory.ignore_missing_slaves:
                return # the client will simply timeout waiting for a response
            response = request.doException(merror.GatewayNoResponse)
        except Exception as ex:
            _logger.debug("Datastore unable to fulfill request: %s" % ex)
            response = request.doException(merror.SlaveFailure)
        #self.framer.populateResult(response)
        response.transaction_id = request.transaction_id
        response.unit_id = request.unit_id
        self._send(response)

    def _send(self, message):
        ''' Send a request (string) to the network

        :param message: The unencoded modbus response
        '''
        if message.should_respond:
            self.factory.control.Counter.BusMessage += 1
            pdu = self.framer.buildPacket(message)
            if _logger.isEnabledFor(logging.DEBUG):
                _logger.debug('send: %s' % b2a_hex(pdu))
            return self.transport.write(pdu)


class ModbusServerFactory(ServerFactory):
    '''
    Builder class for a modbus server

    This also holds the server datastore so that it is
    persisted between connections
    '''

    protocol = ModbusTcpProtocol

    def __init__(self, store, framer=None, identity=None, **kwargs):
        ''' Overloaded initializer for the modbus factory

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param store: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure
        :param ignore_missing_slaves: True to not send errors on a request to a missing slave
        '''
        self.decoder = ServerDecoder()
        self.framer = framer or ModbusSocketFramer
        self.store = store or ModbusServerContext()
        self.control = ModbusControlBlock()
        self.access = ModbusAccessControl()
        self.ignore_missing_slaves = kwargs.get('ignore_missing_slaves', Defaults.IgnoreMissingSlaves)

        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)


#---------------------------------------------------------------------------#
# Modbus UDP Server
#---------------------------------------------------------------------------#
class ModbusUdpProtocol(protocol.DatagramProtocol):
    ''' Implements a modbus udp server in twisted '''

    def __init__(self, store, framer=None, identity=None, **kwargs):
        ''' Overloaded initializer for the modbus factory

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param store: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure
        :param ignore_missing_slaves: True to not send errors on a request to a missing slave
        '''
        framer = framer or ModbusSocketFramer
        self.framer = framer(decoder=ServerDecoder())
        self.store = store or ModbusServerContext()
        self.control = ModbusControlBlock()
        self.access = ModbusAccessControl()
        self.ignore_missing_slaves = kwargs.get('ignore_missing_slaves', Defaults.IgnoreMissingSlaves)

        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

    def datagramReceived(self, data, addr):
        ''' Callback when we receive any data

        :param data: The data sent by the client
        '''
        _logger.debug("Client Connected [%s:%s]" % addr)
        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug(" ".join([hex(byte2int(x)) for x in data]))
        if not self.control.ListenOnly:
            continuation = lambda request: self._execute(request, addr)
            self.framer.processIncomingPacket(data, continuation)

    def _execute(self, request, addr):
        ''' Executes the request and returns the result

        :param request: The decoded request message
        '''
        try:
            context = self.store[request.unit_id]
            response = request.execute(context)
        except NoSuchSlaveException as ex:
            _logger.debug("requested slave does not exist: %s" % request.unit_id )
            if self.ignore_missing_slaves:
                return # the client will simply timeout waiting for a response
            response = request.doException(merror.GatewayNoResponse)
        except Exception as ex:
            _logger.debug("Datastore unable to fulfill request: %s" % ex)
            response = request.doException(merror.SlaveFailure)
        #self.framer.populateResult(response)
        response.transaction_id = request.transaction_id
        response.unit_id = request.unit_id
        self._send(response, addr)

    def _send(self, message, addr):
        ''' Send a request (string) to the network

        :param message: The unencoded modbus response
        :param addr: The (host, port) to send the message to
        '''
        self.control.Counter.BusMessage += 1
        pdu = self.framer.buildPacket(message)
        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug('send: %s' % b2a_hex(pdu))
        return self.transport.write(pdu, addr)


#---------------------------------------------------------------------------#
# Starting Factories
#---------------------------------------------------------------------------#
def _is_main_thread():
    import threading

    if IS_PYTHON3:
        if threading.current_thread() != threading.main_thread():
            _logger.debug("Running in spawned thread")
            return False
    else:
        if not isinstance(threading.current_thread(), threading._MainThread):
            _logger.debug("Running in spawned thread")
            return False
    _logger.debug("Running in Main thread")
    return True


def StartTcpServer(context, identity=None, address=None, console=False, **kwargs):
    ''' Helper method to start the Modbus Async TCP server

    :param context: The server data context
    :param identify: The server identity to use (default empty)
    :param address: An optional (interface, port) to bind to.
    :param console: A flag indicating if you want the debug console
    :param ignore_missing_slaves: True to not send errors on a request to a missing slave
    '''
    from twisted.internet import reactor
    address = address or ("", Defaults.Port)
    framer  = ModbusSocketFramer
    factory = ModbusServerFactory(context, framer, identity, **kwargs)
    if console:
        InstallManagementConsole({'factory': factory})

    _logger.info("Starting Modbus TCP Server on %s:%s" % address)
    reactor.listenTCP(address[1], factory, interface=address[0])
    reactor.run(installSignalHandlers=_is_main_thread())


def StartUdpServer(context, identity=None, address=None, **kwargs):
    ''' Helper method to start the Modbus Async Udp server

    :param context: The server data context
    :param identify: The server identity to use (default empty)
    :param address: An optional (interface, port) to bind to.
    :param ignore_missing_slaves: True to not send errors on a request to a missing slave
    '''
    from twisted.internet import reactor
    address = address or ("", Defaults.Port)
    framer  = ModbusSocketFramer
    server  = ModbusUdpProtocol(context, framer, identity, **kwargs)

    _logger.info("Starting Modbus UDP Server on %s:%s" % address)
    reactor.listenUDP(address[1], server, interface=address[0])
    reactor.run(installSignalHandlers=_is_main_thread())


def StartSerialServer(context, identity=None, framer=ModbusAsciiFramer, **kwargs):
    ''' Helper method to start the Modbus Async Serial server

    :param context: The server data context
    :param identify: The server identity to use (default empty)
    :param framer: The framer to use (default ModbusAsciiFramer)
    :param port: The serial port to attach to
    :param baudrate: The baud rate to use for the serial device
    :param console: A flag indicating if you want the debug console
    :param ignore_missing_slaves: True to not send errors on a request to a missing slave
    '''
    from twisted.internet import reactor
    from twisted.internet.serialport import SerialPort

    port = kwargs.get('port', '/dev/ttyS0')
    baudrate = kwargs.get('baudrate', Defaults.Baudrate)
    console = kwargs.get('console', False)

    _logger.info("Starting Modbus Serial Server on %s" % port)
    factory = ModbusServerFactory(context, framer, identity, **kwargs)
    if console:
        InstallManagementConsole({'factory': factory})

    protocol = factory.buildProtocol(None)
    SerialPort.getHost = lambda self: port # hack for logging
    SerialPort(protocol, port, reactor, baudrate)
    reactor.run(installSignalHandlers=_is_main_thread())


def StopServer():
    """
    Helper method to stop Async Server
    """
    from twisted.internet import reactor
    if _is_main_thread():
        reactor.stop()
        _logger.debug("Stopping server from main thread")
    else:
        reactor.callFromThread(reactor.stop)
        _logger.debug("Stopping Server from another thread")



#---------------------------------------------------------------------------#
# Exported symbols
#---------------------------------------------------------------------------#
__all__ = [
    "StartTcpServer", "StartUdpServer", "StartSerialServer", "StopServer"
]

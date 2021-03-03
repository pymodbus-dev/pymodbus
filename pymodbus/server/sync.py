"""
Implementation of a Threaded Modbus Server
------------------------------------------

"""
from binascii import b2a_hex
import serial
import socket
import ssl
import traceback

from pymodbus.constants import Defaults
from pymodbus.utilities import hexlify_packets
from pymodbus.factory import ServerDecoder
from pymodbus.datastore import ModbusServerContext
from pymodbus.device import ModbusControlBlock
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.transaction import *
from pymodbus.exceptions import NotImplementedException, NoSuchSlaveException
from pymodbus.pdu import ModbusExceptions as merror
from pymodbus.compat import socketserver, byte2int

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
import logging
_logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Protocol Handlers
# --------------------------------------------------------------------------- #

class ModbusBaseRequestHandler(socketserver.BaseRequestHandler):
    """ Implements the modbus server protocol

    This uses the socketserver.BaseRequestHandler to implement
    the client handler.
    """
    running = False
    framer = None
    
    def setup(self):
        """ Callback for when a client connects
        """
        _logger.debug("Client Connected [%s:%s]" % self.client_address)
        self.running = True
        self.framer = self.server.framer(self.server.decoder, client=None)
        self.server.threads.append(self)

    def finish(self):
        """ Callback for when a client disconnects
        """
        _logger.debug("Client Disconnected [%s:%s]" % self.client_address)
        self.server.threads.remove(self)

    def execute(self, request):
        """ The callback to call with the resulting message

        :param request: The decoded request message
        """
        broadcast = False
        try:
            if self.server.broadcast_enable and request.unit_id == 0:
                broadcast = True
                # if broadcasting then execute on all slave contexts, note response will be ignored
                for unit_id in self.server.context.slaves():
                    response = request.execute(self.server.context[unit_id])
            else:
                context = self.server.context[request.unit_id]
                response = request.execute(context)
        except NoSuchSlaveException as ex:
            _logger.debug("requested slave does "
                          "not exist: %s" % request.unit_id )
            if self.server.ignore_missing_slaves:
                return  # the client will simply timeout waiting for a response
            response = request.doException(merror.GatewayNoResponse)
        except Exception as ex:
            _logger.debug("Datastore unable to fulfill request: "
                          "%s; %s", ex, traceback.format_exc())
            response = request.doException(merror.SlaveFailure)
        # no response when broadcasting
        if not broadcast:
            response.transaction_id = request.transaction_id
            response.unit_id = request.unit_id
            self.send(response)

    # ----------------------------------------------------------------------- #
    # Base class implementations
    # ----------------------------------------------------------------------- #
    def handle(self):
        """ Callback when we receive any data
        """
        raise NotImplementedException("Method not implemented"
                                      " by derived class")

    def send(self, message):
        """ Send a request (string) to the network

        :param message: The unencoded modbus response
        """
        raise NotImplementedException("Method not implemented "
                                      "by derived class")


class ModbusSingleRequestHandler(ModbusBaseRequestHandler):
    """ Implements the modbus server protocol

    This uses the socketserver.BaseRequestHandler to implement
    the client handler for a single client(serial clients)
    """
    def handle(self):
        """ Callback when we receive any data
        """
        while self.running:
            try:
                data = self.request.recv(1024)
                if data:
                    units = self.server.context.slaves()
                    if not isinstance(units, (list, tuple)):
                        units = [units]
                    # if broadcast is enabled make sure to process requests to address 0
                    if self.server.broadcast_enable:
                        if 0 not in units:
                            units.append(0)
                    single = self.server.context.single
                    self.framer.processIncomingPacket(data, self.execute,
                                                      units, single=single)
            except Exception as msg:
                # Since we only have a single socket, we cannot exit
                # Clear frame buffer
                self.framer.resetFrame()
                _logger.debug("Error: Socket error occurred %s" % msg)

    def send(self, message):
        """ Send a request (string) to the network

        :param message: The unencoded modbus response
        """
        if message.should_respond:
            # self.server.control.Counter.BusMessage += 1
            pdu = self.framer.buildPacket(message)
            if _logger.isEnabledFor(logging.DEBUG):
                _logger.debug('send: [%s]- %s' % (message, b2a_hex(pdu)))
            return self.request.send(pdu)


class CustomSingleRequestHandler(ModbusSingleRequestHandler):

    def __init__(self, request, client_address, server):
        self.request = request
        self.client_address = client_address
        self.server = server
        self.running = True
        self.setup()


class ModbusConnectedRequestHandler(ModbusBaseRequestHandler):
    """ Implements the modbus server protocol

    This uses the socketserver.BaseRequestHandler to implement
    the client handler for a connected protocol (TCP).
    """

    def handle(self):
        """Callback when we receive any data, until self.running becomes False.
        Blocks indefinitely awaiting data.  If shutdown is required, then the
        global socket.settimeout(<seconds>) may be used, to allow timely
        checking of self.running.  However, since this also affects socket
        connects, if there are outgoing socket connections used in the same
        program, then these will be prevented, if the specfied timeout is too
        short.  Hence, this is unreliable.

        To respond to Modbus...Server.server_close() (which clears each
        handler's self.running), derive from this class to provide an
        alternative handler that awakens from time to time when no input is
        available and checks self.running.
        Use Modbus...Server( handler=... ) keyword to supply the alternative
        request handler class.

        """
        reset_frame = False
        while self.running:
            try:
                units = self.server.context.slaves()
                data = self.request.recv(1024)
                if not data:
                    self.running = False
                else:
                    if not isinstance(units, (list, tuple)):
                        units = [units]
                    # if broadcast is enabled make sure to
                    # process requests to address 0
                    if self.server.broadcast_enable:
                        if 0 not in units:
                            units.append(0)

                if _logger.isEnabledFor(logging.DEBUG):
                    _logger.debug('Handling data: ' + hexlify_packets(data))
                single = self.server.context.single
                self.framer.processIncomingPacket(data, self.execute, units,
                                                  single=single)
            except socket.timeout as msg:
                if _logger.isEnabledFor(logging.DEBUG):
                    _logger.debug("Socket timeout occurred %s", msg)
                reset_frame = True
            except socket.error as msg:
                _logger.error("Socket error occurred %s" % msg)
                self.running = False
            except:
                _logger.error("Socket exception occurred "
                              "%s" % traceback.format_exc() )
                self.running = False
                reset_frame = True
            finally:
                if reset_frame:
                    self.framer.resetFrame()
                    reset_frame = False

    def send(self, message):
        """ Send a request (string) to the network

        :param message: The unencoded modbus response
        """
        if message.should_respond:
            # self.server.control.Counter.BusMessage += 1
            pdu = self.framer.buildPacket(message)
            if _logger.isEnabledFor(logging.DEBUG):
                _logger.debug('send: [%s]- %s' % (message, b2a_hex(pdu)))
            return self.request.send(pdu)


class ModbusDisconnectedRequestHandler(ModbusBaseRequestHandler):
    """ Implements the modbus server protocol

    This uses the socketserver.BaseRequestHandler to implement
    the client handler for a disconnected protocol (UDP). The
    only difference is that we have to specify who to send the
    resulting packet data to.
    """
    socket = None

    def handle(self):
        """ Callback when we receive any data
        """
        reset_frame = False
        while self.running:
            try:
                data, self.socket = self.request
                if not data:
                    self.running = False
                    data = b''
                if _logger.isEnabledFor(logging.DEBUG):
                    _logger.debug('Handling data: ' + hexlify_packets(data))
                # if not self.server.control.ListenOnly:
                units = self.server.context.slaves()
                single = self.server.context.single
                self.framer.processIncomingPacket(data, self.execute,
                                                  units, single=single)
            except socket.timeout: pass
            except socket.error as msg:
                _logger.error("Socket error occurred %s" % msg)
                self.running = False
                reset_frame = True
            except Exception as msg:
                _logger.error(msg)
                self.running = False
                reset_frame = True
            finally:
                # Reset data after processing
                self.request = (None, self.socket)
                if reset_frame:
                    self.framer.resetFrame()
                    reset_frame = False

    def send(self, message):
        """ Send a request (string) to the network

        :param message: The unencoded modbus response
        """
        if message.should_respond:
            #self.server.control.Counter.BusMessage += 1
            pdu = self.framer.buildPacket(message)
            if _logger.isEnabledFor(logging.DEBUG):
                _logger.debug('send: [%s]- %s' % (message, b2a_hex(pdu)))
            return self.socket.sendto(pdu, self.client_address)


# --------------------------------------------------------------------------- #
# Server Implementations
# --------------------------------------------------------------------------- #
class ModbusTcpServer(socketserver.ThreadingTCPServer):
    """
    A modbus threaded tcp socket server

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    def __init__(self, context, framer=None, identity=None,
                 address=None, handler=None, allow_reuse_address=False,
                 **kwargs):
        """ Overloaded initializer for the socket server

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure
        :param address: An optional (interface, port) to bind to.
        :param handler: A handler for each client session; default is
                        ModbusConnectedRequestHandler
        :param allow_reuse_address: Whether the server will allow the
                        reuse of an address.
        :param ignore_missing_slaves: True to not send errors on a request 
                        to a missing slave
        :param broadcast_enable: True to treat unit_id 0 as broadcast address,
                        False to treat 0 as any other unit_id
        """
        self.threads = []
        self.allow_reuse_address = allow_reuse_address
        self.decoder = ServerDecoder()
        self.framer = framer or ModbusSocketFramer
        self.context = context or ModbusServerContext()
        self.control = ModbusControlBlock()
        self.address = address or ("", Defaults.Port)
        self.handler = handler or ModbusConnectedRequestHandler
        self.ignore_missing_slaves = kwargs.get('ignore_missing_slaves',
                                                Defaults.IgnoreMissingSlaves)
        self.broadcast_enable = kwargs.get('broadcast_enable', 
                                           Defaults.broadcast_enable)

        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

        socketserver.ThreadingTCPServer.__init__(self, self.address,
                                                 self.handler)

    def process_request(self, request, client):
        """ Callback for connecting a new client thread

        :param request: The request to handle
        :param client: The address of the client
        """
        _logger.debug("Started thread to serve client at " + str(client))
        socketserver.ThreadingTCPServer.process_request(self, request, client)

    def shutdown(self):
        """ Stops the serve_forever loop.

        Overridden to signal handlers to stop.
        """
        for thread in self.threads:
            thread.running = False
        socketserver.ThreadingTCPServer.shutdown(self)

    def server_close(self):
        """ Callback for stopping the running server
        """
        _logger.debug("Modbus server stopped")
        self.socket.close()
        for thread in self.threads:
            thread.running = False


class ModbusTlsServer(ModbusTcpServer):
    """
    A modbus threaded TLS server

    We inherit and overload the ModbusTcpServer so that we
    can control the client threads as well as have a single
    server context instance.
    """

    def __init__(self, context, framer=None, identity=None,
                 address=None, handler=None, allow_reuse_address=False,
                 sslctx=None, certfile=None, keyfile=None, **kwargs):
        """ Overloaded initializer for the ModbusTcpServer

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure
        :param address: An optional (interface, port) to bind to.
        :param handler: A handler for each client session; default is
                        ModbusConnectedRequestHandler
        :param allow_reuse_address: Whether the server will allow the
                        reuse of an address.
        :param sslctx: The SSLContext to use for TLS (default None and auto
                       create)
        :param certfile: The cert file path for TLS (used if sslctx is None)
        :param keyfile: The key file path for TLS (used if sslctx is None)
        :param ignore_missing_slaves: True to not send errors on a request
                        to a missing slave
        :param broadcast_enable: True to treat unit_id 0 as broadcast address,
                        False to treat 0 as any other unit_id
        """
        self.sslctx = sslctx
        if self.sslctx is None:
            self.sslctx = ssl.create_default_context()
            self.sslctx.load_cert_chain(certfile=certfile, keyfile=keyfile)
            # According to MODBUS/TCP Security Protocol Specification, it is
            # TLSv2 at least
            self.sslctx.options |= ssl.OP_NO_TLSv1_1
            self.sslctx.options |= ssl.OP_NO_TLSv1
            self.sslctx.options |= ssl.OP_NO_SSLv3
            self.sslctx.options |= ssl.OP_NO_SSLv2
        self.sslctx.verify_mode = ssl.CERT_OPTIONAL
        self.sslctx.check_hostname = False

        ModbusTcpServer.__init__(self, context, framer, identity, address,
                                 handler, allow_reuse_address, **kwargs)

    def server_activate(self):
        """ Callback for starting listening over TLS connection
        """
        self.socket = self.sslctx.wrap_socket(self.socket, server_side=True)
        socketserver.ThreadingTCPServer.server_activate(self)


class ModbusUdpServer(socketserver.ThreadingUDPServer):
    """
    A modbus threaded udp socket server

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    def __init__(self, context, framer=None, identity=None, address=None,
                 handler=None, **kwargs):
        """ Overloaded initializer for the socket server

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure
        :param address: An optional (interface, port) to bind to.
        :param handler: A handler for each client session; default is
                            ModbusDisonnectedRequestHandler
        :param ignore_missing_slaves: True to not send errors on a request
                            to a missing slave
        :param broadcast_enable: True to treat unit_id 0 as broadcast address,
                            False to treat 0 as any other unit_id
        """
        self.threads = []
        self.decoder = ServerDecoder()
        self.framer = framer  or ModbusSocketFramer
        self.context = context or ModbusServerContext()
        self.control = ModbusControlBlock()
        self.address = address or ("", Defaults.Port)
        self.handler = handler or ModbusDisconnectedRequestHandler
        self.ignore_missing_slaves = kwargs.get('ignore_missing_slaves',
                                                Defaults.IgnoreMissingSlaves)
        self.broadcast_enable = kwargs.get('broadcast_enable', 
                                           Defaults.broadcast_enable)

        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

        socketserver.ThreadingUDPServer.__init__(self,
            self.address, self.handler)
        # self._BaseServer__shutdown_request = True

    def process_request(self, request, client):
        """ Callback for connecting a new client thread

        :param request: The request to handle
        :param client: The address of the client
        """
        packet, socket = request # TODO I might have to rewrite
        _logger.debug("Started thread to serve client at " + str(client))
        socketserver.ThreadingUDPServer.process_request(self, request, client)

    def server_close(self):
        """ Callback for stopping the running server
        """
        _logger.debug("Modbus server stopped")
        self.socket.close()
        for thread in self.threads:
            thread.running = False


class ModbusSerialServer(object):
    """
    A modbus threaded serial socket server

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    handler = None

    def __init__(self, context, framer=None, identity=None, **kwargs):
        """ Overloaded initializer for the socket server

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure
        :param port: The serial port to attach to
        :param stopbits: The number of stop bits to use
        :param bytesize: The bytesize of the serial messages
        :param parity: Which kind of parity to use
        :param baudrate: The baud rate to use for the serial device
        :param timeout: The timeout to use for the serial device
        :param ignore_missing_slaves: True to not send errors on a request
                            to a missing slave
        :param broadcast_enable: True to treat unit_id 0 as broadcast address,
                            False to treat 0 as any other unit_id
        """
        self.threads = []
        self.decoder = ServerDecoder()
        self.framer = framer or ModbusAsciiFramer
        self.context = context or ModbusServerContext()
        self.control = ModbusControlBlock()

        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

        self.device = kwargs.get('port', 0)
        self.stopbits = kwargs.get('stopbits', Defaults.Stopbits)
        self.bytesize = kwargs.get('bytesize', Defaults.Bytesize)
        self.parity = kwargs.get('parity',   Defaults.Parity)
        self.baudrate = kwargs.get('baudrate', Defaults.Baudrate)
        self.timeout = kwargs.get('timeout',  Defaults.Timeout)
        self.ignore_missing_slaves = kwargs.get('ignore_missing_slaves',
                                                Defaults.IgnoreMissingSlaves)
        self.broadcast_enable = kwargs.get('broadcast_enable',
                                           Defaults.broadcast_enable)
        self.socket = None
        if self._connect():
            self.is_running = True
            self._build_handler()

    def _connect(self):
        """ Connect to the serial server

        :returns: True if connection succeeded, False otherwise
        """
        if self.socket: return True
        try:
            self.socket = serial.Serial(port=self.device,
                                        timeout=self.timeout,
                                        bytesize=self.bytesize,
                                        stopbits=self.stopbits,
                                        baudrate=self.baudrate,
                                        parity=self.parity)
        except serial.SerialException as msg:
            _logger.error(msg)
        return self.socket is not None

    def _build_handler(self):
        """ A helper method to create and monkeypatch
            a serial handler.

        :returns: A patched handler
        """

        request = self.socket
        request.send = request.write
        request.recv = request.read
        self.handler = CustomSingleRequestHandler(request,
                                                  (self.device, self.device),
                                                  self)

    def serve_forever(self):
        """ Callback for connecting a new client thread
        """
        if self._connect():
            _logger.debug("Started thread to serve client")
            if not self.handler:
                self._build_handler()
            while self.is_running:
                if hasattr(self.handler, "response_manipulator"):
                    self.handler.response_manipulator()
                else:
                    self.handler.handle()
        else:
            _logger.error("Error opening serial port , "
                          "Unable to start server!!")

    def server_close(self):
        """ Callback for stopping the running server
        """
        _logger.debug("Modbus server stopped")
        self.is_running = False
        self.handler.finish()
        self.handler.running = False
        self.handler = None
        self.socket.close()


# --------------------------------------------------------------------------- #
# Creation Factories
# --------------------------------------------------------------------------- #
def StartTcpServer(context=None, identity=None, address=None,
                   custom_functions=[], **kwargs):
    """ A factory to start and run a tcp modbus server

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    :param address: An optional (interface, port) to bind to.
    :param custom_functions: An optional list of custom function classes
        supported by server instance.
    :param ignore_missing_slaves: True to not send errors on a request to a
                                      missing slave
    """
    framer = kwargs.pop("framer", ModbusSocketFramer)
    server = ModbusTcpServer(context, framer, identity, address, **kwargs)

    for f in custom_functions:
        server.decoder.register(f)
    server.serve_forever()


def StartTlsServer(context=None, identity=None, address=None, sslctx=None,
                   certfile=None, keyfile=None, custom_functions=[], **kwargs):
    """ A factory to start and run a tls modbus server

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    :param address: An optional (interface, port) to bind to.
    :param sslctx: The SSLContext to use for TLS (default None and auto create)
    :param certfile: The cert file path for TLS (used if sslctx is None)
    :param keyfile: The key file path for TLS (used if sslctx is None)
    :param custom_functions: An optional list of custom function classes
        supported by server instance.
    :param ignore_missing_slaves: True to not send errors on a request to a
                                      missing slave
    """
    framer = kwargs.pop("framer", ModbusTlsFramer)
    server = ModbusTlsServer(context, framer, identity, address, sslctx=sslctx,
                             certfile=certfile, keyfile=keyfile, **kwargs)

    for f in custom_functions:
        server.decoder.register(f)
    server.serve_forever()


def StartUdpServer(context=None, identity=None, address=None,
                   custom_functions=[], **kwargs):
    """ A factory to start and run a udp modbus server

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    :param address: An optional (interface, port) to bind to.
    :param custom_functions: An optional list of custom function classes
        supported by server instance.
    :param framer: The framer to operate with (default ModbusSocketFramer)
    :param ignore_missing_slaves: True to not send errors on a request
                                    to a missing slave
    """
    framer = kwargs.pop('framer', ModbusSocketFramer)
    server = ModbusUdpServer(context, framer, identity, address, **kwargs)
    for f in custom_functions:
        server.decoder.register(f)
    server.serve_forever()


def StartSerialServer(context=None, identity=None,  custom_functions=[],
                      **kwargs):
    """ A factory to start and run a serial modbus server

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    :param custom_functions: An optional list of custom function classes
        supported by server instance.
    :param framer: The framer to operate with (default ModbusAsciiFramer)
    :param port: The serial port to attach to
    :param stopbits: The number of stop bits to use
    :param bytesize: The bytesize of the serial messages
    :param parity: Which kind of parity to use
    :param baudrate: The baud rate to use for the serial device
    :param timeout: The timeout to use for the serial device
    :param ignore_missing_slaves: True to not send errors on a request to a
                                  missing slave
    """
    framer = kwargs.pop('framer', ModbusAsciiFramer)
    server = ModbusSerialServer(context, framer, identity, **kwargs)
    for f in custom_functions:
        server.decoder.register(f)
    server.serve_forever()

# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #


__all__ = [
    "StartTcpServer", "StartTlsServer", "StartUdpServer", "StartSerialServer"
]


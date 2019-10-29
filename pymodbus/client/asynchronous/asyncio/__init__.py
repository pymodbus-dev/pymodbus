"""
Asynchronous framework adapter for asyncio.
"""
import socket
import asyncio
import functools
from pymodbus.exceptions import ConnectionException
from pymodbus.client.asynchronous.mixins import AsyncModbusClientMixin
from pymodbus.compat import byte2int
import logging

_logger = logging.getLogger(__name__)

DGRAM_TYPE = socket.SocketKind.SOCK_DGRAM


class BaseModbusAsyncClientProtocol(AsyncModbusClientMixin):
    """
    Asyncio specific implementation of asynchronous modbus client protocol.
    """

    #: Factory that created this instance.
    factory = None
    transport = None

    def connection_made(self, transport):
        """
        Called when a connection is made.

        The transport argument is the transport representing the connection.
        :param transport:
        :return:
        """
        self.transport = transport
        self._connectionMade()

        if self.factory:
            self.factory.protocol_made_connection(self)

    def connection_lost(self, reason):
        """
        Called when the connection is lost or closed.

        The argument is either an exception object or None
        :param reason:
        :return:
        """
        self.transport = None
        self._connectionLost(reason)

        if self.factory:
            self.factory.protocol_lost_connection(self)

    def data_received(self, data):
        """
        Called when some data is received.
        data is a non-empty bytes object containing the incoming data.
        :param data:
        :return:
        """
        self._dataReceived(data)

    def create_future(self):
        """
        Helper function to create asyncio Future object
        :return:
        """
        return asyncio.Future()

    def resolve_future(self, f, result):
        """
        Resolves the completed future and sets the result
        :param f:
        :param result:
        :return:
        """
        if not f.done():
            f.set_result(result)

    def raise_future(self, f, exc):
        """
        Sets exception of a future if not done
        :param f:
        :param exc:
        :return:
        """
        if not f.done():
            f.set_exception(exc)

    def _connectionMade(self):
        """
        Called upon a successful client connection.
        """
        _logger.debug("Client connected to modbus server")
        self._connected = True

    def _connectionLost(self, reason):
        """
        Called upon a client disconnect

        :param reason: The reason for the disconnect
        """
        _logger.debug(
            "Client disconnected from modbus server: %s" % reason)
        self._connected = False
        for tid in list(self.transaction):
            self.raise_future(self.transaction.getTransaction(tid),
                              ConnectionException(
                                  'Connection lost during request'))

    @property
    def connected(self):
        """
        Return connection status.
        """
        return self._connected

    def write_transport(self, packet):
        return self.transport.write(packet)

    def execute(self, request, **kwargs):
        """
        Starts the producer to send the next request to
        consumer.write(Frame(request))
        """
        request.transaction_id = self.transaction.getNextTID()
        packet = self.framer.buildPacket(request)
        _logger.debug("send: " + " ".join([hex(byte2int(x)) for x in packet]))
        self.write_transport(packet)
        return self._buildResponse(request.transaction_id)

    def _dataReceived(self, data):
        ''' Get response, check for valid message, decode result

        :param data: The data returned from the server
        '''
        _logger.debug("recv: " + " ".join([hex(byte2int(x)) for x in data]))
        unit = self.framer.decode_data(data).get("uid", 0)
        self.framer.processIncomingPacket(data, self._handleResponse, unit=unit)

    def _handleResponse(self, reply, **kwargs):
        """
        Handle the processed response and link to correct deferred

        :param reply: The reply to process
        """
        if reply is not None:
            tid = reply.transaction_id
            handler = self.transaction.getTransaction(tid)
            if handler:
                self.resolve_future(handler, reply)
            else:
                _logger.debug("Unrequested message: " + str(reply))

    def _buildResponse(self, tid):
        """
        Helper method to return a deferred response
        for the current request.

        :param tid: The transaction identifier for this response
        :returns: A defer linked to the latest request
        """
        f = self.create_future()
        if not self._connected:
            self.raise_future(f, ConnectionException(
                'Client is not connected'))
        else:
            self.transaction.addTransaction(f, tid)
        return f

    def close(self):
        self.transport.close()
        self._connected = False


class ModbusClientProtocol(BaseModbusAsyncClientProtocol, asyncio.Protocol):
    """
    Asyncio specific implementation of asynchronous modbus client protocol.
    """

    #: Factory that created this instance.
    factory = None
    transport = None

    def data_received(self, data):
        """
        Called when some data is received.
        data is a non-empty bytes object containing the incoming data.
        :param data:
        :return:
        """
        self._dataReceived(data)


class ModbusUdpClientProtocol(BaseModbusAsyncClientProtocol,
                              asyncio.DatagramProtocol):
    """
    Asyncio specific implementation of asynchronous modbus udp client protocol.
    """

    #: Factory that created this instance.
    factory = None

    def __init__(self, host=None, port=0, **kwargs):
        self.host = host
        self.port = port
        super(self.__class__, self).__init__(**kwargs)

    def datagram_received(self, data, addr):
        self._dataReceived(data)

    def write_transport(self, packet):
        return self.transport.sendto(packet)


class ReconnectingAsyncioModbusTcpClient(object):
    """
    Client to connect to modbus device repeatedly over TCP/IP."
    """
    #: Minimum delay in milli seconds before reconnect is attempted.
    DELAY_MIN_MS = 100
    #: Maximum delay in milli seconds before reconnect is attempted.
    DELAY_MAX_MS = 1000 * 60 * 5

    def __init__(self, protocol_class=None, loop=None):
        """
        Initialize ReconnectingAsyncioModbusTcpClient
        :param protocol_class: Protocol used to talk to modbus device.
        :param loop: Event loop to use
        """
        #: Protocol used to talk to modbus device.
        self.protocol_class = protocol_class or ModbusClientProtocol
        #: Current protocol instance.
        self.protocol = None
        #: Event loop to use.
        self.loop = loop or asyncio.get_event_loop()
        self.host = None
        self.port = 0
        self.connected = False
        #: Reconnect delay in milli seconds.
        self.delay_ms = self.DELAY_MIN_MS

    def reset_delay(self):
        """
        Resets wait before next reconnect to minimal period.
        """
        self.delay_ms = self.DELAY_MIN_MS

    @asyncio.coroutine
    def start(self, host, port=502):
        """
        Initiates connection to start client
        :param host:
        :param port:
        :return:
        """
        # force reconnect if required:
        self.stop()

        _logger.debug('Connecting to %s:%s.' % (host, port))
        self.host = host
        self.port = port
        yield from self._connect()

    def stop(self):
        """
        Stops client
        :return:
        """
        # prevent reconnect:
        self.host = None

        if self.connected:
            if self.protocol:
                if self.protocol.transport:
                    self.protocol.transport.close()

    def _create_protocol(self):
        """
        Factory function to create initialized protocol instance.
        """
        protocol = self.protocol_class()
        protocol.factory = self
        return protocol

    @asyncio.coroutine
    def _connect(self):
        _logger.debug('Connecting.')
        try:
            yield from self.loop.create_connection(self._create_protocol,
                                                   self.host,
                                                   self.port)
        except Exception as ex:
            _logger.warning('Failed to connect: %s' % ex)
            asyncio.ensure_future(self._reconnect(), loop=self.loop)
        else:
            _logger.info('Connected to %s:%s.' % (self.host, self.port))
            self.reset_delay()

    def protocol_made_connection(self, protocol):
        """
        Protocol notification of successful connection.
        """
        _logger.info('Protocol made connection.')
        if not self.connected:
            self.connected = True
            self.protocol = protocol
        else:
            _logger.error('Factory protocol connect '
                          'callback called while connected.')

    def protocol_lost_connection(self, protocol):
        """
        Protocol notification of lost connection.
        """
        if self.connected:
            _logger.info('Protocol lost connection.')
            if protocol is not self.protocol:
                _logger.error('Factory protocol callback called '
                              'from unexpected protocol instance.')

            self.connected = False
            self.protocol = None
            if self.host:
                asyncio.ensure_future(self._reconnect(), loop=self.loop)
        else:
            _logger.error('Factory protocol disconnect callback called while not connected.')

    @asyncio.coroutine
    def _reconnect(self):
        _logger.debug('Waiting %d ms before next '
                      'connection attempt.' % self.delay_ms)
        yield from asyncio.sleep(self.delay_ms / 1000)
        self.delay_ms = min(2 * self.delay_ms, self.DELAY_MAX_MS)
        yield from self._connect()


class AsyncioModbusTcpClient(object):
    """Client to connect to modbus device over TCP/IP."""

    def __init__(self, host=None, port=502, protocol_class=None, loop=None):
        """
        Initializes Asyncio Modbus Tcp Client
        :param host: Host IP address
        :param port: Port to connect
        :param protocol_class: Protocol used to talk to modbus device.
        :param loop: Asyncio Event loop
        """
        #: Protocol used to talk to modbus device.
        self.protocol_class = protocol_class or ModbusClientProtocol
        #: Current protocol instance.
        self.protocol = None
        #: Event loop to use.
        self.loop = loop or asyncio.get_event_loop()

        self.host = host
        self.port = port

        self.connected = False

    def stop(self):
        """
        Stops the client
        :return:
        """
        if self.connected:
            if self.protocol:
                if self.protocol.transport:
                    self.protocol.transport.close()

    def _create_protocol(self):
        """
        Factory function to create initialized protocol instance.
        """
        protocol = self.protocol_class()
        protocol.factory = self
        return protocol

    @asyncio.coroutine
    def connect(self):
        """
        Connect and start Async client
        :return:
        """
        _logger.debug('Connecting.')
        try:
            yield from self.loop.create_connection(self._create_protocol,
                                                   self.host,
                                                   self.port)
            _logger.info('Connected to %s:%s.' % (self.host, self.port))
        except Exception as ex:
            _logger.warning('Failed to connect: %s' % ex)
            # asyncio.asynchronous(self._reconnect(), loop=self.loop)

    def protocol_made_connection(self, protocol):
        """
        Protocol notification of successful connection.
        """
        _logger.info('Protocol made connection.')
        if not self.connected:
            self.connected = True
            self.protocol = protocol
        else:
            _logger.error('Factory protocol connect '
                          'callback called while connected.')

    def protocol_lost_connection(self, protocol):
        """
        Protocol notification of lost connection.
        """
        if self.connected:
            _logger.info('Protocol lost connection.')
            if protocol is not self.protocol:
                _logger.error('Factory protocol callback called'
                              ' from unexpected protocol instance.')

            self.connected = False
            self.protocol = None
            # if self.host:
            #     asyncio.asynchronous(self._reconnect(), loop=self.loop)
        else:
            _logger.error('Factory protocol disconnect'
                          ' callback called while not connected.')


class ReconnectingAsyncioModbusUdpClient(object):
    """
    Client to connect to modbus device repeatedly over UDP.
    """

    #: Reconnect delay in milli seconds.
    delay_ms = 0

    #: Maximum delay in milli seconds before reconnect is attempted.
    DELAY_MAX_MS = 1000 * 60 * 5

    def __init__(self, protocol_class=None, loop=None):
        """
        Initializes ReconnectingAsyncioModbusUdpClient
        :param protocol_class: Protocol used to talk to modbus device.
        :param loop: Asyncio Event loop
        """
        #: Protocol used to talk to modbus device.
        self.protocol_class = protocol_class or ModbusUdpClientProtocol
        #: Current protocol instance.
        self.protocol = None
        #: Event loop to use.
        self.loop = loop or asyncio.get_event_loop()

        self.host = None
        self.port = 0

        self.connected = False
        self.reset_delay()

    def reset_delay(self):
        """
        Resets wait before next reconnect to minimal period.
        """
        self.delay_ms = 100

    @asyncio.coroutine
    def start(self, host, port=502):
        """
        Start reconnecting asynchronous udp client
        :param host: Host IP to connect
        :param port: Host port to connect
        :return:
        """
        # force reconnect if required:
        self.stop()

        _logger.debug('Connecting to %s:%s.' % (host, port))

        # getaddrinfo returns a list of tuples
        # - [(family, type, proto, canonname, sockaddr),]
        # We want sockaddr which is a (ip, port) tuple
        # udp needs ip addresses, not hostnames
        addrinfo = yield from self.loop.getaddrinfo(host,
                                                    port,
                                                    type=DGRAM_TYPE)
        self.host, self.port = addrinfo[0][-1]

        yield from self._connect()

    def stop(self):
        """
        Stops connection and prevents reconnect
        :return:
        """
        # prevent reconnect:
        self.host = None

        if self.connected:
            if self.protocol:
                if self.protocol.transport:
                    self.protocol.transport.close()

    def _create_protocol(self, host=None, port=0):
        """
        Factory function to create initialized protocol instance.
        """
        protocol = self.protocol_class()
        protocol.host = host
        protocol.port = port
        protocol.factory = self
        return protocol

    @asyncio.coroutine
    def _connect(self):
        _logger.debug('Connecting.')
        try:
            yield from self.loop.create_datagram_endpoint(
                functools.partial(self._create_protocol,
                                  host=self.host,
                                  port=self.port),
                remote_addr=(self.host, self.port)
            )
            _logger.info('Connected to %s:%s.' % (self.host, self.port))
        except Exception as ex:
            _logger.warning('Failed to connect: %s' % ex)
            asyncio.ensure_future(self._reconnect(), loop=self.loop)

    def protocol_made_connection(self, protocol):
        """
        Protocol notification of successful connection.
        """
        _logger.info('Protocol made connection.')
        if not self.connected:
            self.connected = True
            self.protocol = protocol
        else:
            _logger.error('Factory protocol connect callback '
                          'called while connected.')

    def protocol_lost_connection(self, protocol):
        """
        Protocol notification of lost connection.
        """
        if self.connected:
            _logger.info('Protocol lost connection.')
            if protocol is not self.protocol:
                _logger.error('Factory protocol callback called '
                              'from unexpected protocol instance.')

            self.connected = False
            self.protocol = None
            if self.host:
                asyncio.ensure_future(self._reconnect(), loop=self.loop)
        else:
            _logger.error('Factory protocol disconnect '
                          'callback called while not connected.')

    @asyncio.coroutine
    def _reconnect(self):
        _logger.debug('Waiting %d ms before next '
                      'connection attempt.' % self.delay_ms)
        yield from asyncio.sleep(self.delay_ms / 1000)
        self.delay_ms = min(2 * self.delay_ms, self.DELAY_MAX_MS)
        yield from self._connect()


class AsyncioModbusUdpClient(object):
    """
    Client to connect to modbus device over UDP.
    """

    def __init__(self, host=None, port=502, protocol_class=None, loop=None):
        """
        Initializes Asyncio Modbus UDP Client
        :param host: Host IP address
        :param port: Port to connect
        :param protocol_class: Protocol used to talk to modbus device.
        :param loop: Asyncio Event loop
        """
        #: Protocol used to talk to modbus device.
        self.protocol_class = protocol_class or ModbusUdpClientProtocol
        #: Current protocol instance.
        self.protocol = None
        #: Event loop to use.
        self.loop = loop or asyncio.get_event_loop()

        self.host = host
        self.port = port

        self.connected = False

    def stop(self):
        """
        Stops connection
        :return:
        """
        # prevent reconnect:
        # self.host = None

        if self.connected:
            if self.protocol:
                if self.protocol.transport:
                    self.protocol.transport.close()

    def _create_protocol(self, host=None, port=0):
        """
        Factory function to create initialized protocol instance.
        """
        protocol = self.protocol_class()
        protocol.host = host
        protocol.port = port
        protocol.factory = self
        return protocol

    @asyncio.coroutine
    def connect(self):
        _logger.debug('Connecting.')
        try:
            addrinfo = yield from self.loop.getaddrinfo(
                self.host,
                self.port,
                type=DGRAM_TYPE)
            _host, _port = addrinfo[0][-1]
            yield from self.loop.create_datagram_endpoint(
                functools.partial(self._create_protocol,
                                  host=_host, port=_port),
                remote_addr=(self.host, self.port)
            )
            _logger.info('Connected to %s:%s.' % (self.host, self.port))
        except Exception as ex:
            _logger.warning('Failed to connect: %s' % ex)
            # asyncio.asynchronous(self._reconnect(), loop=self.loop)

    def protocol_made_connection(self, protocol):
        """
        Protocol notification of successful connection.
        """
        _logger.info('Protocol made connection.')
        if not self.connected:
            self.connected = True
            self.protocol = protocol
        else:
            _logger.error('Factory protocol connect '
                          'callback called while connected.')

    def protocol_lost_connection(self, protocol):
        """
        Protocol notification of lost connection.
        """
        if self.connected:
            _logger.info('Protocol lost connection.')
            if protocol is not self.protocol:
                _logger.error('Factory protocol callback '
                              'called from unexpected protocol instance.')

            self.connected = False
            self.protocol = None
            # if self.host:
            #    asyncio.asynchronous(self._reconnect(), loop=self.loop)
        else:
            _logger.error('Factory protocol disconnect '
                          'callback called while not connected.')


class AsyncioModbusSerialClient(object):
    """
    Client to connect to modbus device over serial.
    """
    transport = None
    framer = None

    def __init__(self, port, protocol_class=None, framer=None,  loop=None,
                 baudrate=9600, bytesize=8, parity='N', stopbits=1):
        """
        Initializes Asyncio Modbus Serial Client
        :param port: Port to connect
        :param protocol_class: Protocol used to talk to modbus device.
        :param framer: Framer to use
        :param loop: Asyncio Event loop
        """
        #: Protocol used to talk to modbus device.
        self.protocol_class = protocol_class or ModbusClientProtocol
        #: Current protocol instance.
        self.protocol = None
        #: Event loop to use.
        self.loop = loop or asyncio.get_event_loop()
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.framer = framer
        self._connected_event = asyncio.Event()

    def stop(self):
        """
        Stops connection
        :return:
        """
        if self._connected:
            if self.protocol:
                if self.protocol.transport:
                    self.protocol.transport.close()

    def _create_protocol(self):
        protocol = self.protocol_class(framer=self.framer)
        protocol.factory = self
        return protocol

    @property
    def _connected(self):
        return self._connected_event.is_set()

    @asyncio.coroutine
    def connect(self):
        """
        Connect Async client
        :return:
        """
        _logger.debug('Connecting.')
        try:
            from serial_asyncio import create_serial_connection

            yield from create_serial_connection(
                self.loop, self._create_protocol, self.port, baudrate=self.baudrate,
                bytesize=self.bytesize, stopbits=self.stopbits, parity=self.parity
            )
            yield from self._connected_event.wait()
            _logger.info('Connected to %s', self.port)
        except Exception as ex:
            _logger.warning('Failed to connect: %s', ex)

    def protocol_made_connection(self, protocol):
        """
        Protocol notification of successful connection.
        """
        _logger.info('Protocol made connection.')
        if not self._connected:
            self._connected_event.set()
            self.protocol = protocol
        else:
            _logger.error('Factory protocol connect '
                          'callback called while connected.')

    def protocol_lost_connection(self, protocol):
        """
        Protocol notification of lost connection.
        """
        if self._connected:
            _logger.info('Protocol lost connection.')
            if protocol is not self.protocol:
                _logger.error('Factory protocol callback called'
                              ' from unexpected protocol instance.')

            self._connected_event.clear()
            self.protocol = None
            # if self.host:
            #     asyncio.asynchronous(self._reconnect(), loop=self.loop)
        else:
            _logger.error('Factory protocol disconnect callback '
                          'called while not connected.')


@asyncio.coroutine
def init_tcp_client(proto_cls, loop, host, port, **kwargs):
    """
    Helper function to initialize tcp client
    :param proto_cls:
    :param loop:
    :param host:
    :param port:
    :param kwargs:
    :return:
    """
    client = ReconnectingAsyncioModbusTcpClient(protocol_class=proto_cls,
                                                loop=loop)
    yield from client.start(host, port)
    return client


@asyncio.coroutine
def init_udp_client(proto_cls, loop, host, port, **kwargs):
    """
    Helper function to initialize UDP client
    :param proto_cls:
    :param loop:
    :param host:
    :param port:
    :param kwargs:
    :return:
    """
    client = ReconnectingAsyncioModbusUdpClient(protocol_class=proto_cls,
                                                loop=loop)
    yield from client.start(host, port)
    return client

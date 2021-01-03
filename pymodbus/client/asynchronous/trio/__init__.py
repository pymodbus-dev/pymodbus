import contextlib
import functools
import logging

import trio

from pymodbus.client.asynchronous.mixins import AsyncModbusClientMixin
from pymodbus.exceptions import ConnectionException
from pymodbus.utilities import hexlify_packets

_logger = logging.getLogger(__name__)


class BaseModbusAsyncClientProtocol(AsyncModbusClientMixin):
    """
    Trio specific implementation of asynchronous modbus client protocol.
    """

    #: Factory that created this instance.
    factory = None
    transport = None

    async def execute(self, request=None):
        """
        Executes requests asynchronously
        :param request:
        :return:
        """
        # with trio.fail_after(seconds=self._timeout):
        resp = await self._execute(request)

        return resp

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

    def _connectionMade(self):
        """
        Called upon a successful client connection.
        """
        _logger.debug("Client connected to modbus server")
        self._connected = True

    async def _execute(self, request, **kwargs):
        """
        Starts the producer to send the next request to
        consumer.write(Frame(request))
        """
        request.transaction_id = self.transaction.getNextTID()
        packet = self.framer.buildPacket(request)
        _logger.debug("send: " + hexlify_packets(packet))
        await self.write_transport(packet)
        return await self._buildResponse(request.transaction_id)

    def _dataReceived(self, data):
        ''' Get response, check for valid message, decode result

        :param data: The data returned from the server
        '''
        _logger.debug("recv: " + hexlify_packets(data))
        unit = self.framer.decode_data(data).get("unit", 0)
        self.framer.processIncomingPacket(data, self._handleResponse, unit=unit)

    async def write_transport(self, packet):
        return await self.transport.send(packet)

    def _handleResponse(self, reply, **kwargs):
        """
        Handle the processed response and link to correct deferred

        :param reply: The reply to process
        """
        if reply is not None:
            tid = reply.transaction_id
            handler = self.transaction.getTransaction(tid)
            if handler:
                handler.value = reply
                handler.event.set()
            else:
                _logger.debug("Unrequested message: " + str(reply))

    async def _buildResponse(self, tid):
        """
        Helper method to return a deferred response
        for the current request.

        :param tid: The transaction identifier for this response
        :returns: A defer linked to the latest request
        """
        if not self._connected:
            raise ConnectionException('Client is not connected')

        class EventAndValue:
            def __init__(self):
                self.event = trio.Event()
                self.value = self

        event_and_value = EventAndValue()
        self.transaction.addTransaction(event_and_value, tid)
        await event_and_value.event.wait()
        return event_and_value.value


class ModbusClientProtocol(BaseModbusAsyncClientProtocol):
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


# class ModbusUdpClientProtocol(BaseModbusAsyncClientProtocol):
#     """
#     Asyncio specific implementation of asynchronous modbus udp client protocol.
#     """
#
#     #: Factory that created this instance.
#     factory = None
#
#     def __init__(self, host=None, port=0, **kwargs):
#         self.host = host
#         self.port = port
#         super(self.__class__, self).__init__(**kwargs)
#
#     def datagram_received(self, data, addr):
#         self._dataReceived(data)
#
#     def write_transport(self, packet):
#         return self.transport.sendto(packet)


class TrioModbusTcpClient(object):
    """Client to connect to modbus device over TCP/IP."""

    def __init__(self, host=None, port=502, protocol_class=None, loop=None):
        """
        Initializes Asyncio Modbus Tcp Client
        :param host: Host IP address
        :param port: Port to connect
        :param protocol_class: Protocol used to talk to modbus device.
        """
        #: Protocol used to talk to modbus device.
        self.protocol_class = protocol_class or ModbusClientProtocol
        #: Current protocol instance.
        self.protocol = None
        #: Event loop to use.

        self.host = host
        self.port = port

        self.connected = False

    @contextlib.asynccontextmanager
    async def manage_connection(self):
        async with trio.open_nursery() as nursery:
            self.protocol = self._create_protocol()
            client_stream = await trio.open_tcp_stream(self.host, self.port)

            write_send_channel, write_receive_channel = trio.open_memory_channel(0)
            async with write_send_channel:
                self.protocol.connection_made(transport=write_send_channel)
                nursery.start_soon(
                    functools.partial(
                        self.sender,
                        stream=client_stream,
                        channel=write_receive_channel,
                    ),
                )
                nursery.start_soon(
                    functools.partial(self.receiver, stream=client_stream),
                )

                yield self.protocol

            nursery.cancel_scope.cancel()

    async def sender(self, stream, channel):
        async with channel:
            async for data in channel:
                await stream.send_all(data)

    async def receiver(self, stream):
        async for data in stream:
            self.protocol.data_received(data)
            # await channel.send(data)

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

    # # @asyncio.coroutine
    # def connect(self):
    #     """
    #     Connect and start Async client
    #     :return:
    #     """
    #     _logger.debug('Connecting.')
    #     try:
    #         yield from self.loop.create_connection(self._create_protocol,
    #                                                self.host,
    #                                                self.port)
    #         _logger.info('Connected to %s:%s.' % (self.host, self.port))
    #     except Exception as ex:
    #         _logger.warning('Failed to connect: %s' % ex)
    #         # asyncio.asynchronous(self._reconnect(), loop=self.loop)

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


def init_tcp_client(proto_cls, host, port, **kwargs):
    """
    Helper function to initialize tcp client
    :param proto_cls:
    :param loop:
    :param host:
    :param port:
    :param kwargs:
    :return:
    """
    client = TrioModbusTcpClient(protocol_class=proto_cls, host=host, port=port)
    return client

import functools
import logging

import async_generator
import trio

from pymodbus.client.asynchronous.mixins import AsyncModbusClientMixin
from pymodbus.exceptions import ConnectionException
from pymodbus.utilities import hexlify_packets

_logger = logging.getLogger(__name__)


class EventAndValue:
    def __init__(self):
        self.event = trio.Event()
        self.value = self

    def __call__(self, value):
        self.value = value
        self.event.set()


class BaseModbusAsyncClientProtocol(AsyncModbusClientMixin):
    """
    Trio specific implementation of asynchronous modbus client protocol.
    """

    #: Factory that created this instance.
    factory = None
    transport = None
    data = b''

    async def execute(self, request=None):
        request.transaction_id = self.transaction.getNextTID()
        packet = self.framer.buildPacket(request)
        _logger.debug("send: " + hexlify_packets(packet))
        # TODO: should we retry on trio.BusyResourceError?
        await self.transport.send_all(packet)
        response = await self._build_response(request.transaction_id)
        return response

    def connection_made(self, transport):
        """
        Called when a connection is made.

        The transport argument is the transport representing the connection.
        :param transport:
        :return:
        """
        self.transport = transport
        _logger.debug("Client connected to modbus server")
        self._connected = True

        if self.factory:
            self.factory.protocol_made_connection(self)

    # TODO: _connectionLost looks like functionality to have somewhere

    def _data_received(self, data):
        ''' Get response, check for valid message, decode result

        :param data: The data returned from the server
        '''
        _logger.debug("recv: " + hexlify_packets(data))

        # TODO: trying to help out the framer here by buffering up a bit but it
        #       is insufficient and still fails down below.
        self.data += data
        decoded = self.framer.decode_data(self.data)
        if decoded == {}:
            return

        unit = decoded.get("unit", 0)
        self.framer.processIncomingPacket(self.data, self._handle_response, unit=unit)
        self.data = b''

    def _handle_response(self, reply, **kwargs):
        """
        Handle the processed response and link to correct deferred

        :param reply: The reply to process
        """
        if reply is not None:
            tid = reply.transaction_id
            handler = self.transaction.getTransaction(tid)
            if handler:
                handler(reply)
            else:
                _logger.debug("Unrequested message: " + str(reply))

    async def _build_response(self, tid):
        """
        Helper method to return a deferred response
        for the current request.

        :param tid: The transaction identifier for this response
        :returns: A defer linked to the latest request
        """
        if not self._connected:
            raise ConnectionException('Client is not connected')

        event_and_value = EventAndValue()
        self.transaction.addTransaction(event_and_value, tid)
        await event_and_value.event.wait()
        return event_and_value.value


class ModbusTcpClientProtocol(BaseModbusAsyncClientProtocol):
    """
    Trio specific implementation of asynchronous modbus client protocol.
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
        self._data_received(data)


# TODO: implement UDP


class TrioModbusTcpClient:
    """Client to connect to modbus device over TCP/IP."""

    def __init__(self, host=None, port=502, protocol_class=None, loop=None):
        """
        Initializes Asyncio Modbus Tcp Client
        :param host: Host IP address
        :param port: Port to connect
        :param protocol_class: Protocol used to talk to modbus device.
        """
        #: Protocol used to talk to modbus device.
        self.protocol_class = protocol_class or ModbusTcpClientProtocol
        #: Current protocol instance.
        self.protocol = None
        #: Event loop to use.

        self.host = host
        self.port = port

        self.connected = False

    @async_generator.asynccontextmanager
    async def manage_connection(self):
        async with trio.open_nursery() as nursery:
            self.protocol = self._create_protocol()
            client_stream = await trio.open_tcp_stream(self.host, self.port)

            self.protocol.connection_made(transport=client_stream)
            nursery.start_soon(
                functools.partial(self.receiver, stream=client_stream),
            )

            yield self.protocol

            nursery.cancel_scope.cancel()

    async def receiver(self, stream):
        async for data in stream:
            self.protocol.data_received(data)

            # seems like this should work due to the framer but it doesn't
            # for d in data:
            #     self.protocol.data_received(bytes([d]))

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

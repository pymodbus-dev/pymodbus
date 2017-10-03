from __future__ import unicode_literals

import socket

import logging

from tornado import gen
from tornado.concurrent import Future
from tornado.ioloop import IOLoop
from tornado.iostream import IOStream

from pymodbus.client.async.tcp import ModbusTCPClientMixin
from pymodbus.client.common import ModbusClientMixin
from pymodbus.exceptions import ConnectionException


LOGGER = logging.getLogger(__name__)


class AsyncTornadoModbusTCPClient(ModbusTCPClientMixin, ModbusClientMixin):

    @gen.coroutine
    def connect(self):
        """Connect to the socket identified by host and port

        :returns: Future
        :rtype:
        """
        conn = socket.create_connection((self.host, self.port),
                                        timeout=self.timeout,
                                        source_address=self.source_address)

        self.stream = IOStream(conn, io_loop=IOLoop.current())
        self.stream.read_until_close(None,
                                     streaming_callback=self.data_received)
        self._connected = True

        raise gen.Return(self)

    def close(self):
        """Closes the underlying IOStream
        """
        LOGGER.debug("Client disconnected")
        if self.stream:
            self.stream.close_fd()

        self.stream = None

    def data_received(self, *args):
        data = args[0] if len(args) > 0 else None

        if not data:
            return

        self.framer.processIncomingPacket(data, self._handle_response)

    def execute(self, request=None):
        request.transaction_id = self.transaction.getNextTID()
        packet = self.framer.buildPacket(request)
        self.stream.write(packet)
        return self._build_response(request.transaction_id)

    def _handle_response(self, reply):
        if reply is not None:
            tid = reply.transaction_id
            future = self.transaction.getTransaction(tid)
            if future:
                future.set_result(reply)
            else:
                LOGGER.debug("Unrequested message: {}".format(reply))

    def _build_response(self, tid):
        f = Future()

        if not self._connected:
            f.set_exception(ConnectionException("Client is not connected"))
            return f

        self.transaction.addTransaction(f, tid)
        return f


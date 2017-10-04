from __future__ import unicode_literals

import abc

import logging

from tornado import gen
from tornado.concurrent import Future
from tornado.ioloop import IOLoop
from tornado.iostream import IOStream

from pymodbus.client.async import AsyncModbusClientMixin
from pymodbus.exceptions import ConnectionException

LOGGER = logging.getLogger(__name__)


class BaseTornadoClient(AsyncModbusClientMixin):
    @abc.abstractmethod
    def get_socket(self):
        """return instance of the socket to connect to
        """

    @gen.coroutine
    def connect(self):
        """Connect to the socket identified by host and port

        :returns: Future
        :rtype: tornado.concurrent.Future
        """
        conn = self.get_socket()
        self.stream = IOStream(conn, io_loop=IOLoop.current())
        self.stream.connect((self.host, self.port))
        self.stream.read_until_close(None,
                                     streaming_callback=self.on_receive)
        self._connected = True
        LOGGER.debug("Client connected")

        raise gen.Return(self)

    def on_receive(self, *args):
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

    def close(self):
        """Closes the underlying IOStream
        """
        LOGGER.debug("Client disconnected")
        if self.stream:
            self.stream.close_fd()

        self.stream = None

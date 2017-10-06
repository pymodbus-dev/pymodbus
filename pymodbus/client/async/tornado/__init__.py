from __future__ import unicode_literals

import abc

import logging

import socket
from serial import Serial
from tornado import gen
from tornado.concurrent import Future
from tornado.ioloop import IOLoop
from tornado.iostream import IOStream
from tornado.iostream import BaseIOStream

from pymodbus.client.async import AsyncModbusClientMixin, AsyncModbusSerialClientMixin
from pymodbus.exceptions import ConnectionException

LOGGER = logging.getLogger(__name__)


class BaseTornadoClient(AsyncModbusClientMixin):
    stream = None
    io_loop = None

    def __init__(self, *args, **kwargs):
        self.ioloop = kwargs.pop("ioloop")
        super(BaseTornadoClient, self).__init__(*args, **kwargs)

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
        self.stream = IOStream(conn, io_loop=self.ioloop or IOLoop.current())
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

    def _handle_response(self, reply, **kwargs):
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


class BaseTornadoSerialClient(AsyncModbusSerialClientMixin):
    stream = None
    io_loop = None

    def __init__(self, *args, **kwargs):
        self.ioloop = kwargs.pop("ioloop")
        super(BaseTornadoSerialClient, self).__init__(*args, **kwargs)

    @abc.abstractmethod
    def get_socket(self):
        """return instance of the socket to connect to
        """

    def on_receive(self, *args):
        pass

    def execute(self, request=None):
        f = Future()
        request.transaction_id = self.transaction.getNextTID()

        def callback(*args):
            print("in callback - {}".format(request.transaction_id))
            while True:
                waiting = self.stream.connection.in_waiting
                if waiting:
                    data = self.stream.connection.read(waiting)
                    self.framer.processIncomingPacket(data, self._handle_response, tid=request.transaction_id)
                    break

        packet = self.framer.buildPacket(request)
        self.stream.write(packet, callback=callback)
        self.transaction.addTransaction(f, request.transaction_id)
        return f

    def _handle_response(self, reply, **kwargs):
        if reply is not None:
            tid = reply.transaction_id
            future = self.transaction.getTransaction(tid)
            if future:
                future.set_result(reply)
            else:
                LOGGER.debug("Unrequested message: {}".format(reply))

    def close(self):
        """Closes the underlying IOStream
        """
        LOGGER.debug("Client disconnected")
        if self.stream:
            self.stream.close_fd()

        self.stream = None


class SerialIOStream(BaseIOStream):

    def __init__(self, connection, *args, **kwargs):
        self.connection = connection
        super(SerialIOStream, self).__init__(*args, **kwargs)

    def fileno(self):
        return self.connection.fileno()

    def close_fd(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def read_from_fd(self):
        try:
            chunk = self.connection.readline()
        except Exception:
            return None

        return chunk

    def write_to_fd(self, data):
        try:
            return self.connection.write(data)
        except  Exception as e:
            LOGGER.error(e)


class AsyncModbusSerialClient(BaseTornadoSerialClient):
    def get_socket(self):
        return Serial(port=self.port, **self.serial_settings)

    @gen.coroutine
    def connect(self):
        """Connect to the socket identified by host and port

        :returns: Future
        :rtype: tornado.concurrent.Future
        """
        conn = self.get_socket()
        if self.io_loop is None:
            self.io_loop = IOLoop.current()
        try:
            self.stream = SerialIOStream(conn, io_loop=self.io_loop)
        except Exception as e:
            LOGGER.exception(e)

        self._connected = True
        LOGGER.debug("Client connected")

        raise gen.Return(self)


class AsyncModbusTCPClient(BaseTornadoClient):
    def get_socket(self):
        return socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)


class AsyncModbusUDPClient(BaseTornadoClient):
    def get_socket(self):
        return socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
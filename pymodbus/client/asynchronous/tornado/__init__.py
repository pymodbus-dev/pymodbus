"""
Asynchronous framework adapter for tornado.
"""
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

from pymodbus.client.asynchronous.mixins import (AsyncModbusClientMixin,
                                                 AsyncModbusSerialClientMixin)
from pymodbus.exceptions import ConnectionException
from pymodbus.compat import byte2int

LOGGER = logging.getLogger(__name__)


class BaseTornadoClient(AsyncModbusClientMixin):
    """
    Base Tornado client
    """
    stream = None
    io_loop = None

    def __init__(self, *args, **kwargs):
        """
        Initializes BaseTornadoClient.
        ioloop to be passed as part of kwargs ('ioloop')
        :param args:
        :param kwargs:
        """
        self.io_loop = kwargs.pop("ioloop", None)
        super(BaseTornadoClient, self).__init__(*args, **kwargs)

    @abc.abstractmethod
    def get_socket(self):
        """
        return instance of the socket to connect to
        """

    @gen.coroutine
    def connect(self):
        """
        Connect to the socket identified by host and port

        :returns: Future
        :rtype: tornado.concurrent.Future
        """
        conn = self.get_socket()
        self.stream = IOStream(conn, io_loop=self.io_loop or IOLoop.current())
        self.stream.connect((self.host, self.port))
        self.stream.read_until_close(None,
                                     streaming_callback=self.on_receive)
        self._connected = True
        LOGGER.debug("Client connected")

        raise gen.Return(self)

    def on_receive(self, *args):
        """
        On data recieve call back
        :param args: data received
        :return:
        """
        data = args[0] if len(args) > 0 else None

        if not data:
            return
        LOGGER.debug("recv: " + " ".join([hex(byte2int(x)) for x in data]))
        unit = self.framer.decode_data(data).get("uid", 0)
        self.framer.processIncomingPacket(data, self._handle_response, unit=unit)

    def execute(self, request=None):
        """
        Executes a transaction
        :param request:
        :return:
        """
        request.transaction_id = self.transaction.getNextTID()
        packet = self.framer.buildPacket(request)
        LOGGER.debug("send: " + " ".join([hex(byte2int(x)) for x in packet]))
        self.stream.write(packet)
        return self._build_response(request.transaction_id)

    def _handle_response(self, reply, **kwargs):
        """
        Handle response received
        :param reply:
        :param kwargs:
        :return:
        """
        if reply is not None:
            tid = reply.transaction_id
            future = self.transaction.getTransaction(tid)
            if future:
                future.set_result(reply)
            else:
                LOGGER.debug("Unrequested message: {}".format(reply))

    def _build_response(self, tid):
        """
        Builds a future response
        :param tid:
        :return:
        """
        f = Future()

        if not self._connected:
            f.set_exception(ConnectionException("Client is not connected"))
            return f

        self.transaction.addTransaction(f, tid)
        return f

    def close(self):
        """
        Closes the underlying IOStream
        """
        LOGGER.debug("Client disconnected")
        if self.stream:
            self.stream.close_fd()

        self.stream = None
        self._connected = False


class BaseTornadoSerialClient(AsyncModbusSerialClientMixin):
    """
    Base Tonado serial client
    """
    stream = None
    io_loop = None

    def __init__(self, *args, **kwargs):
        """
        Initializes BaseTornadoSerialClient.
        ioloop to be passed as part of kwargs ('ioloop')
        :param args:
        :param kwargs:
        """
        self.io_loop = kwargs.pop("ioloop", None)
        super(BaseTornadoSerialClient, self).__init__(*args, **kwargs)

    @abc.abstractmethod
    def get_socket(self):
        """
        return instance of the socket to connect to
        """

    def on_receive(self, *args):
        # Will be handled ine execute method
        pass

    def execute(self, request=None):
        """
        Executes a transaction
        :param request: Request to be written on to the bus
        :return:
        """
        request.transaction_id = self.transaction.getNextTID()

        def callback(*args):
            LOGGER.debug("in callback - {}".format(request.transaction_id))
            while True:
                waiting = self.stream.connection.in_waiting
                if waiting:
                    data = self.stream.connection.read(waiting)
                    LOGGER.debug(
                        "recv: " + " ".join([hex(byte2int(x)) for x in data]))
                    unit = self.framer.decode_data(data).get("uid", 0)
                    self.framer.processIncomingPacket(
                        data,
                        self._handle_response,
                        unit,
                        tid=request.transaction_id
                    )
                    break

        packet = self.framer.buildPacket(request)
        LOGGER.debug("send: " + " ".join([hex(byte2int(x)) for x in packet]))
        self.stream.write(packet, callback=callback)
        f = self._build_response(request.transaction_id)
        return f

    def _handle_response(self, reply, **kwargs):
        """
        Handles a received response and updates a future
        :param reply: Reply received
        :param kwargs:
        :return:
        """
        if reply is not None:
            tid = reply.transaction_id
            future = self.transaction.getTransaction(tid)
            if future:
                future.set_result(reply)
            else:
                LOGGER.debug("Unrequested message: {}".format(reply))

    def _build_response(self, tid):
        """
        Prepare for a response, returns a future
        :param tid:
        :return: Future
        """
        f = Future()

        if not self._connected:
            f.set_exception(ConnectionException("Client is not connected"))
            return f

        self.transaction.addTransaction(f, tid)
        return f

    def close(self):
        """
        Closes the underlying IOStream
        """
        LOGGER.debug("Client disconnected")
        if self.stream:
            self.stream.close_fd()

        self.stream = None
        self._connected = False


class SerialIOStream(BaseIOStream):
    """
    Serial IO Stream class to control and handle serial connections
     over tornado
    """
    def __init__(self, connection, *args, **kwargs):
        """
        Initializes Serial IO Stream
        :param connection: serial object
        :param args:
        :param kwargs:
        """
        self.connection = connection
        super(SerialIOStream, self).__init__(*args, **kwargs)

    def fileno(self):
        """
        Returns serial fd
        :return:
        """
        return self.connection.fileno()

    def close_fd(self):
        """
        Closes a serial Fd
        :return:
        """
        if self.connection:
            self.connection.close()
            self.connection = None

    def read_from_fd(self):
        """
        Reads from a fd
        :return:
        """
        try:
            chunk = self.connection.readline()
        except Exception:
            return None

        return chunk

    def write_to_fd(self, data):
        """
        Writes to a fd
        :param data:
        :return:
        """
        try:
            return self.connection.write(data)
        except  Exception as e:
            LOGGER.error(e)


class AsyncModbusSerialClient(BaseTornadoSerialClient):
    """
    Tornado based asynchronous serial client
    """
    def get_socket(self):
        """
        Creates Pyserial object
        :return: serial object
        """
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
    """
    Tornado based Async tcp client
    """
    def get_socket(self):
        """
        Creates socket object
        :return: socket
        """
        return socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)


class AsyncModbusUDPClient(BaseTornadoClient):
    """
    Tornado based Async UDP client
    """
    def get_socket(self):
        """
        Create socket object
        :return: socket
        """
        return socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
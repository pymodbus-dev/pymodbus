"""Asynchronous framework adapter for tornado."""
import logging
import abc
import time
import socket
from serial import Serial
from tornado import gen
from tornado.concurrent import Future
from tornado.ioloop import IOLoop
from tornado.iostream import IOStream
from tornado.iostream import BaseIOStream

from pymodbus.client.asynchronous.mixins import (
    AsyncModbusClientMixin,
    AsyncModbusSerialClientMixin,
)

from pymodbus.exceptions import ConnectionException, ModbusIOException, TimeOutException
from pymodbus.utilities import hexlify_packets, ModbusTransactionState
from pymodbus.constants import Defaults


_logger = logging.getLogger(__name__)


class BaseTornadoClient(AsyncModbusClientMixin):
    """Base Tornado client."""

    stream = None
    io_loop = None

    def __init__(self, *args, **kwargs):
        """Initialize BaseTornadoClient.

        ioloop to be passed as part of kwargs ("ioloop")
        :param args:
        :param kwargs:
        """
        self.io_loop = kwargs.pop("ioloop", None)
        super().__init__(*args, **kwargs)

    @abc.abstractmethod
    def get_socket(self):
        """Return instance of the socket to connect to."""

    @gen.coroutine
    def connect(self):
        """Connect to the socket identified by host and port.

        :returns: Future
        :rtype: tornado.concurrent.Future
        """
        conn = self.get_socket()
        self.stream = IOStream(conn, io_loop=self.io_loop or IOLoop.current())
        self.stream.connect((self.host, self.port))
        self.stream.read_until_close(None, streaming_callback=self.on_receive)
        self._connected = True
        _logger.debug("Client connected")

        raise gen.Return(self)

    def on_receive(self, *args):
        """Receive call back.

        :param args: data received
        :return:
        """
        if not (data := args[0] if len(args) > 0 else None):
            return
        txt = f"recv: {hexlify_packets(data)}"
        _logger.debug(txt)
        unit = self.framer.decode_data(data).get("unit", 0)
        self.framer.processIncomingPacket(data, self._handle_response, unit=unit)

    def execute(self, request=None):
        """Execute a transaction.

        :param request:
        :return:
        """
        request.transaction_id = self.transaction.getNextTID()
        packet = self.framer.buildPacket(request)
        txt = f"send: {hexlify_packets(packet)}"
        _logger.debug(txt)
        self.stream.write(packet)
        return self._build_response(request.transaction_id)

    def _handle_response(self, reply, **kwargs):  # pylint: disable=unused-argument
        """Handle response received.

        :param reply:
        :param kwargs:
        :return:
        """
        if reply is not None:
            tid = reply.transaction_id
            if future := self.transaction.getTransaction(tid):
                future.set_result(reply)
            else:
                txt = f"Unrequested message: {reply}"
                _logger.debug(txt)

    def _build_response(self, tid):
        """Build a future response.

        :param tid:
        :return:
        """
        my_future = Future()

        if not self._connected:
            my_future.set_exception(ConnectionException("Client is not connected"))
            return my_future

        self.transaction.addTransaction(my_future, tid)
        return my_future

    def close(self):
        """Close the underlying IOStream."""
        _logger.debug("Client disconnected")
        if self.stream:
            self.stream.close_fd()

        self.stream = None
        self._connected = False


class BaseTornadoSerialClient(AsyncModbusSerialClientMixin):
    """Base Tonado serial client."""

    stream = None
    io_loop = None

    def __init__(self, *args, **kwargs):
        """Initialize BaseTornadoSerialClient.

        ioloop to be passed as part of kwargs ("ioloop")
        :param args:
        :param kwargs:
        """
        self.io_loop = kwargs.pop("ioloop", None)
        super().__init__(*args, **kwargs)

    @abc.abstractmethod
    def get_socket(self):
        """Return instance of the socket to connect to."""

    def on_receive(self, *args):
        """Handle (to be) in the execute method."""

    def execute(self, request=None):
        """Execute a transaction.

        :param request: Request to be written on to the bus
        :return:
        """
        request.transaction_id = self.transaction.getNextTID()

        def callback(*args):  # pylint: disable=unused-argument
            txt = f"in callback - {request.transaction_id}"
            _logger.debug(txt)
            while True:
                if waiting := self.stream.connection.in_waiting:
                    data = self.stream.connection.read(waiting)
                    txt = f"recv: {hexlify_packets(data)}"
                    _logger.debug(txt)
                    unit = self.framer.decode_data(data).get("uid", 0)
                    self.framer.processIncomingPacket(
                        data, self._handle_response, unit, tid=request.transaction_id
                    )
                    break

        packet = self.framer.buildPacket(request)
        txt = f"send: {hexlify_packets(packet)}"
        _logger.debug(txt)
        self.stream.write(packet, callback=callback)
        response = self._build_response(request.transaction_id)
        return response

    def _handle_response(self, reply, **kwargs):  # pylint: disable=unused-argument
        """Handle a received response and updates a future.

        :param reply: Reply received
        :param kwargs:
        :return:
        """
        if reply is not None:
            tid = reply.transaction_id
            if future := self.transaction.getTransaction(tid):
                future.set_result(reply)
            else:
                txt = f"Unrequested message: {reply}"
                _logger.debug(txt)

    def _build_response(self, tid):
        """Prepare for a response, returns a future.

        :param tid:
        :return: Future
        """
        my_future = Future()

        if not self._connected:
            my_future.set_exception(ConnectionException("Client is not connected"))
            return my_future

        self.transaction.addTransaction(my_future, tid)
        return my_future

    def close(self):
        """Close the underlying IOStream."""
        _logger.debug("Client disconnected")
        if self.stream:
            self.stream.close_fd()

        self.stream = None
        self._connected = False


class SerialIOStream(BaseIOStream):
    """Serial IO Stream class to control and handle serial connections over tornado."""

    def __init__(self, connection, *args, **kwargs):
        """Initialize Serial IO Stream.

        :param connection: serial object
        :param args:
        :param kwargs:
        """
        self.connection = connection
        super().__init__(*args, **kwargs)

    def fileno(self):
        """Return serial fd.

        :return:
        """
        return self.connection.fileno()

    def close_fd(self):
        """Close a serial Fd.

        :return:
        """
        if self.connection:
            self.connection.close()
            self.connection = None

    def read_from_fd(self):
        """Read from a fd

        :return:
        """
        try:
            chunk = self.connection.readline()
        except Exception:  # pylint: disable=broad-except
            return None

        return chunk

    def write_to_fd(self, data):
        """Write to a fd.

        :param data:
        :return:
        """
        try:
            return self.connection.write(data)
        except Exception as exc:  # pylint: disable=broad-except
            _logger.error(exc)
        return None


class AsyncModbusSerialClient(BaseTornadoSerialClient):
    """Tornado based asynchronous serial client."""

    def __init__(self, *args, **kwargs):
        """Initialize AsyncModbusSerialClient.

        :param args:
        :param kwargs:
        """
        self.state = ModbusTransactionState.IDLE
        self.timeout = kwargs.get("timeout", Defaults.Timeout)
        self.baudrate = kwargs.get("baudrate", Defaults.Baudrate)
        if self.baudrate > 19200:
            self.silent_interval = 1.75 / 1000  # ms
        else:
            self._t0 = float((1 + 8 + 2)) / self.baudrate
            self.silent_interval = 3.5 * self._t0
        self.silent_interval = round(self.silent_interval, 6)
        self.last_frame_end = 0.0
        super().__init__(*args, **kwargs)

    def get_socket(self):
        """Create Pyserial object

        :return: serial object
        """
        return Serial(port=self.port, **self.serial_settings)

    @gen.coroutine
    def connect(self):
        """Connect to the socket identified by host and port.

        :returns: Future
        :rtype: tornado.concurrent.Future
        """
        conn = self.get_socket()
        if self.io_loop is None:
            self.io_loop = IOLoop.current()
        try:
            self.stream = SerialIOStream(conn, io_loop=self.io_loop)
        except Exception as exc:  # pylint: disable=broad-except
            _logger.exception(exc)

        self._connected = True
        _logger.debug("Client connected")

        raise gen.Return(self)

    def execute(self, request=None):  # NOSONAR
        """Execute a transaction.

        :param request: Request to be written on to the bus
        :return:
        """
        request.transaction_id = self.transaction.getNextTID()

        def _clear_timer():
            """Clear serial waiting timeout."""
            if self.timeout_handle:
                self.io_loop.remove_timeout(self.timeout_handle)
                self.timeout_handle = (  # pylint: disable=attribute-defined-outside-init
                    None
                )

        def _on_timeout():
            """Got timeout while waiting data from serial port."""
            _logger.warning("serial receive timeout")
            _clear_timer()
            if self.stream:
                self.io_loop.remove_handler(self.stream.fileno())
            self.framer.resetFrame()
            if transaction := self.transaction.getTransaction(request.transaction_id):
                transaction.set_exception(TimeOutException())

        def _on_write_done():
            """Set up reader part after successful write to the serial."""
            _logger.debug("frame sent, waiting for a reply")
            self.last_frame_end = round(time.time(), 6)
            self.state = ModbusTransactionState.WAITING_FOR_REPLY
            self.io_loop.add_handler(self.stream.fileno(), _on_receive, IOLoop.READ)

        def _on_fd_error(fd, *args):
            _clear_timer()
            self.io_loop.remove_handler(fd)
            self.close()
            self.transaction.getTransaction(request.transaction_id).set_exception(
                ModbusIOException(*args)
            )

        def _on_receive(fd, events):
            """Check new data in serial buffer to read or serial port closed."""
            if events & IOLoop.ERROR:
                _on_fd_error(fd)
                return

            try:
                if waiting := self.stream.connection.in_waiting:
                    data = self.stream.connection.read(waiting)
                    txt = f"recv: {hexlify_packets(data)}"
                    _logger.debug(txt)
                    self.last_frame_end = round(time.time(), 6)
            except OSError as exc:
                _on_fd_error(fd, exc)
                return

            self.framer.addToFrame(data)

            # check if we have regular frame or modbus exception
            fcode = self.framer.decode_data(self.framer.getRawFrame()).get("fcode", 0)
            if fcode and (
                (
                    fcode > 0x80
                    and len(self.framer.getRawFrame()) == exception_response_length
                )
                or (
                    len(self.framer.getRawFrame()) == expected_response_length
                )
            ):
                _clear_timer()
                self.io_loop.remove_handler(fd)
                self.state = ModbusTransactionState.IDLE
                self.framer.processIncomingPacket(
                    b"",  # already sent via addToFrame()
                    self._handle_response,
                    0,  # don"t care when `single=True`
                    single=True,
                    tid=request.transaction_id,
                )

        packet = self.framer.buildPacket(request)
        response = self._build_response(request.transaction_id)

        response_pdu_size = request.get_response_pdu_size()
        expected_response_length = self.transaction._calculate_response_length(  # pylint: disable=protected-access
            response_pdu_size
        )
        txt = f"expected_response_length = {expected_response_length}"
        _logger.debug(txt)

        # NOSONAR TODO: calculate once
        exception_response_length = (
            self.transaction._calculate_exception_length()  # pylint: disable=protected-access
        )

        if self.timeout:
            self.timeout_handle = self.io_loop.add_timeout(  # pylint: disable=attribute-defined-outside-init
                time.time() + self.timeout, _on_timeout
            )
        self._send_packet(packet, callback=_on_write_done)

        return response

    def _send_packet(self, message, callback):
        """Send packets on the bus with 3.5char delay between frames.

        :param message: Message to be sent over the bus
        :return:
        """

        @gen.coroutine
        def sleep(timeout):
            yield gen.sleep(timeout)

        try:
            if waiting := self.stream.connection.in_waiting:
                result = self.stream.connection.read(waiting)
                txt = f"Cleanup recv buffer before send: {hexlify_packets(result)}"
                _logger.info(txt)
        except OSError as exc:
            self.transaction.getTransaction(message.transaction_id).set_exception(
                ModbusIOException(exc)
            )
            return

        start = time.time()
        if self.last_frame_end:
            if (waittime := self.last_frame_end + self.silent_interval - start) > 0:
                txt = f"Waiting for 3.5 char before next send - {waittime} ms"
                _logger.debug(txt)
                sleep(waittime)

        self.state = ModbusTransactionState.SENDING
        txt = f"send: {hexlify_packets(message)}"
        _logger.debug(txt)
        self.stream.write(message, callback)


class AsyncModbusTCPClient(BaseTornadoClient):
    """Tornado based Async tcp client."""

    def get_socket(self):
        """Create socket object.

        :return: socket
        """
        return socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)


class AsyncModbusUDPClient(BaseTornadoClient):
    """Tornado based Async UDP client."""

    def get_socket(self):
        """Create socket object.

        :return: socket
        """
        return socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

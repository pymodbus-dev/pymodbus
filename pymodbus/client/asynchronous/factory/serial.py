"""Factory to create asynchronous serial clients based on twisted/tornado/asyncio."""
import logging
import asyncio

from pymodbus.client.asynchronous import schedulers
from pymodbus.client.asynchronous.thread import EventLoopThread
from pymodbus.client.asynchronous.async_io import (
    ModbusClientProtocol,
    AsyncioModbusSerialClient,
)
from pymodbus.factory import ClientDecoder


_logger = logging.getLogger(__name__)


def reactor_factory(port, framer, **kwargs):
    """Create twisted serial asynchronous client.

    :param port: Serial port
    :param framer: Modbus Framer
    :param kwargs:
    :return: event_loop_thread and twisted serial client
    """
    from twisted.internet import reactor  # pylint: disable=import-outside-toplevel
    from twisted.internet.serialport import (  # pylint: disable=import-outside-toplevel
        SerialPort,
    )
    from twisted.internet.protocol import (  # pylint: disable=import-outside-toplevel
        ClientFactory,
    )

    class SerialClientFactory(ClientFactory):
        """Define serial client factory."""

        def __init__(self, framer, proto_cls):
            """Remember things necessary for building a protocols."""
            self.proto_cls = proto_cls
            self.framer = framer

        def buildProtocol(self):  # pylint: disable=arguments-differ
            """Create a protocol and start the reading cycle-"""
            proto = self.proto_cls(self.framer)
            proto.factory = self
            return proto

    class SerialModbusClient(SerialPort):  # pylint: disable=abstract-method
        """Define serial client."""

        def __init__(self, framer, *args, **kwargs):
            """Initialize the client and start listening on the serial port.

            :param factory: The factory to build clients with
            """
            self.decoder = ClientDecoder()
            proto_cls = kwargs.pop("proto_cls", None)
            proto = SerialClientFactory(framer, proto_cls).buildProtocol()
            SerialPort.__init__(self, proto, *args, **kwargs)

    proto = EventLoopThread(
        "reactor",
        reactor.run,  # pylint: disable=no-member
        reactor.stop,  # pylint: disable=no-member
        installSignalHandlers=0,
    )
    ser_client = SerialModbusClient(framer, port, reactor, **kwargs)

    return proto, ser_client


def io_loop_factory(port=None, framer=None, **kwargs):
    """Create Tornado based asynchronous serial clients.

    :param port:  Serial port
    :param framer: Modbus Framer
    :param kwargs:
    :return: event_loop_thread and tornado future
    """
    from tornado.ioloop import IOLoop  # pylint: disable=import-outside-toplevel
    from pymodbus.client.asynchronous.tornado import (  # pylint: disable=import-outside-toplevel
        AsyncModbusSerialClient as Client,
    )

    ioloop = IOLoop()
    protocol = EventLoopThread("ioloop", ioloop.start, ioloop.stop)
    protocol.start()
    client = Client(port=port, framer=framer, ioloop=ioloop, **kwargs)

    future = client.connect()

    return protocol, future


def async_io_factory(port=None, framer=None, **kwargs):
    """Create asyncio based asynchronous serial clients.

    :param port:  Serial port
    :param framer: Modbus Framer
    :param kwargs: Serial port options
    :return: asyncio event loop and serial client
    """
    try:
        loop = kwargs.pop("loop", None) or asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()

    proto_cls = kwargs.get("proto_cls") or ModbusClientProtocol

    client = AsyncioModbusSerialClient(port, proto_cls, framer, loop, **kwargs)
    coro = client.connect
    if not loop.is_running():
        loop.run_until_complete(coro())
    else:  # loop is not asyncio.get_event_loop():
        future = asyncio.run_coroutine_threadsafe(coro, loop=loop)
        future.result()

    return loop, client


def get_factory(scheduler):
    """Get protocol factory based on the backend scheduler being used.

    :param scheduler: REACTOR/IO_LOOP/ASYNC_IO
    :return:
    """
    if scheduler == schedulers.REACTOR:
        return reactor_factory
    if scheduler == schedulers.IO_LOOP:
        return io_loop_factory
    if scheduler == schedulers.ASYNC_IO:
        return async_io_factory

    txt = f"Allowed Schedulers: {schedulers.REACTOR}, {schedulers.IO_LOOP}, {schedulers.ASYNC_IO}"
    _logger.warning(txt)
    txt = f'Invalid Scheduler "{scheduler}"'
    raise Exception(txt)  # NOSONAR

"""
Factory to create asynchronous serial clients based on twisted/tornado/asyncio
"""
from __future__ import unicode_literals
from __future__ import absolute_import

import logging
import sys
import time
from pymodbus.client.asynchronous import schedulers
from pymodbus.client.asynchronous.thread import EventLoopThread

LOGGER = logging.getLogger(__name__)


def reactor_factory(port, framer, **kwargs):
    """
    Factory to create twisted serial asynchronous client
    :param port: Serial port
    :param framer: Modbus Framer
    :param kwargs:
    :return: event_loop_thread and twisted serial client
    """
    from twisted.internet import reactor
    from twisted.internet.serialport import SerialPort
    from twisted.internet.protocol import ClientFactory
    from pymodbus.factory import ClientDecoder

    class SerialClientFactory(ClientFactory):
        def __init__(self, framer, proto_cls):
            ''' Remember things necessary for building a protocols '''
            self.proto_cls = proto_cls
            self.framer = framer

        def buildProtocol(self):
            ''' Create a protocol and start the reading cycle '''
            proto = self.proto_cls(self.framer)
            proto.factory = self
            return proto

    if sys.platform == "win32":
        import serial
        import serial.win32

        class RegularFileSerial(serial.Serial):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.captured_args = args
                self.captured_kwargs = kwargs

            def _reconfigurePort(self):
                pass

            def _reconfigure_port(self):
                pass

        class RegularFileSerialPort(SerialPort):
            _serialFactory = RegularFileSerial

            def __init__(self, *args, **kwargs):
                cbInQue = kwargs.get("cbInQue")

                if "cbInQue" in kwargs:
                    del kwargs["cbInQue"]

                self.comstat = serial.win32.COMSTAT
                self.comstat.cbInQue = cbInQue

                super().__init__(*args, **kwargs)

            def _clearCommError(self):
                return True, self.comstat

        class SerialModbusClient(RegularFileSerialPort):

            def __init__(self, framer, *args, **kwargs):
                ''' Setup the client and start listening on the serial port

                :param factory: The factory to build clients with
                '''
                self.decoder = ClientDecoder()
                proto_cls = kwargs.pop("proto_cls", None)
                proto = SerialClientFactory(framer, proto_cls).buildProtocol()
                super(SerialModbusClient, self).__init__(proto, *args, **kwargs)
    else:
        class SerialModbusClient(SerialPort):

            def __init__(self, framer, *args, **kwargs):
                ''' Setup the client and start listening on the serial port

                :param factory: The factory to build clients with
                '''
                self.decoder = ClientDecoder()
                proto_cls = kwargs.pop("proto_cls", None)
                proto = SerialClientFactory(framer, proto_cls).buildProtocol()
                super(SerialModbusClient, self).__init__(proto, *args, **kwargs)

    proto = EventLoopThread("reactor", reactor.run, reactor.stop,
                            installSignalHandlers=0)
    ser_client = SerialModbusClient(framer, port, reactor, **kwargs)

    return proto, ser_client


def io_loop_factory(port=None, framer=None, **kwargs):
    """
    Factory to create Tornado based asynchronous serial clients
    :param port:  Serial port
    :param framer: Modbus Framer
    :param kwargs:
    :return: event_loop_thread and tornado future
    """

    from tornado.ioloop import IOLoop
    from pymodbus.client.asynchronous.tornado import (AsyncModbusSerialClient as
                                               Client)

    ioloop = IOLoop()
    protocol = EventLoopThread("ioloop", ioloop.start, ioloop.stop)
    protocol.start()
    client = Client(port=port, framer=framer, ioloop=ioloop, **kwargs)

    future = client.connect()

    return protocol, future


def async_io_factory(port=None, framer=None, **kwargs):
    """
    Factory to create asyncio based asynchronous serial clients
    :param port:  Serial port
    :param framer: Modbus Framer
    :param kwargs: Serial port options
    :return: asyncio event loop and serial client
    """
    import asyncio
    from pymodbus.client.asynchronous.async_io import (ModbusClientProtocol,
                                                       AsyncioModbusSerialClient)
    loop = kwargs.pop("loop", None) or asyncio.get_event_loop()
    proto_cls = kwargs.pop("proto_cls", None) or ModbusClientProtocol

    try:
        from serial_asyncio import create_serial_connection
    except ImportError:
        LOGGER.critical("pyserial-asyncio is not installed, "
                        "install with 'pip install pyserial-asyncio")
        import sys
        sys.exit(1)

    client = AsyncioModbusSerialClient(port, proto_cls, framer, loop, **kwargs)
    coro = client.connect()
    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(coro, loop=loop)
        future.result()
    else:
        loop.run_until_complete(coro)
    return loop, client


def get_factory(scheduler):
    """
    Gets protocol factory based on the backend scheduler being used
    :param scheduler: REACTOR/IO_LOOP/ASYNC_IO
    :return:
    """
    if scheduler == schedulers.REACTOR:
        return reactor_factory
    elif scheduler == schedulers.IO_LOOP:
        return io_loop_factory
    elif scheduler == schedulers.ASYNC_IO:
        return async_io_factory
    else:
        LOGGER.warning("Allowed Schedulers: {}, {}, {}".format(
            schedulers.REACTOR, schedulers.IO_LOOP, schedulers.ASYNC_IO
        ))
        raise Exception("Invalid Scheduler '{}'".format(scheduler))

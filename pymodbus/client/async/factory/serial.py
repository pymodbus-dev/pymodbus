"""
Copyright (c) 2017 by Riptide I/O
All rights reserved.
"""
from __future__ import unicode_literals
from __future__ import absolute_import

import logging

from pymodbus.client.async import schedulers
from pymodbus.client.async.thread import EventLoopThread
from pymodbus.constants import Defaults


LOGGER = logging.getLogger(__name__)


def reactor_factory(framer, port, **kwargs):
    from twisted.internet import reactor, serialport
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

    class SerialModbusClient(serialport.SerialPort):

        def __init__(self, framer, *args, **kwargs):
            ''' Setup the client and start listening on the serial port

            :param factory: The factory to build clients with
            '''
            self.decoder = ClientDecoder()
            proto_cls = kwargs.pop("proto_cls", None)
            proto = SerialClientFactory(framer, proto_cls).buildProtocol()
            serialport.SerialPort.__init__(self, proto, *args, **kwargs)

    proto = EventLoopThread("reactor", reactor.run, reactor.stop,
                            installSignalHandlers=0)
    s = SerialModbusClient(framer, port, reactor, **kwargs)

    return s, proto


def io_loop_factory(port=None, framer=None, **kwargs):
    from tornado.ioloop import IOLoop
    from pymodbus.client.async.tornado import AsyncModbusSerialClient as \
        Client

    ioloop = IOLoop()
    protocol = EventLoopThread("ioloop", ioloop.start, ioloop.stop)
    protocol.start()

    client = Client(port=port, framer=framer, ioloop=ioloop, **kwargs)

    future = client.connect()

    return protocol, future


def async_io_factory(host="127.0.0.1", port=Defaults.Port, framer=None,
                     source_address=None, timeout=None, **kwargs):
    pass


def get_factory(scheduler):
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


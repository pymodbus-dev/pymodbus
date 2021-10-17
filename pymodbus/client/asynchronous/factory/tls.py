"""
Factory to create asynchronous tls clients based on asyncio
"""
from __future__ import unicode_literals
from __future__ import absolute_import

import logging

from pymodbus.client.asynchronous import schedulers
from pymodbus.client.asynchronous.thread import EventLoopThread
from pymodbus.constants import Defaults

LOGGER = logging.getLogger(__name__)

def async_io_factory(host="127.0.0.1", port=Defaults.TLSPort, sslctx=None,
                     server_hostname=None, framer=None, **kwargs):
    """
    Factory to create asyncio based asynchronous tls clients
    :param host: Host IP address
    :param port: Port
    :param sslctx: The SSLContext to use for TLS (default None and auto create)
    :param server_hostname: Target server's name matched for certificate
    :param framer: Modbus Framer
    :param source_address: Bind address
    :param timeout: Timeout in seconds
    :param kwargs:
    :return: asyncio event loop and tcp client
    """
    import asyncio
    from pymodbus.client.asynchronous.async_io import init_tls_client
    loop = kwargs.pop("loop", None) or asyncio.new_event_loop()
    proto_cls = kwargs.pop("proto_cls", None)
    if not loop.is_running():
        asyncio.set_event_loop(loop)
        cor = init_tls_client(proto_cls, loop, host, port, sslctx, server_hostname,
                              framer, **kwargs)
        client = loop.run_until_complete(asyncio.gather(cor))[0]
    else:
        cor = init_tls_client(proto_cls, loop, host, port, sslctx, server_hostname,
                              framer, **kwargs)
        future = asyncio.run_coroutine_threadsafe(cor, loop=loop)
        client = future.result()

    return loop, client


def get_factory(scheduler):
    """
    Gets protocol factory based on the backend scheduler being used
    :param scheduler: ASYNC_IO
    :return
    """
    if scheduler == schedulers.ASYNC_IO:
        return async_io_factory
    else:
        LOGGER.warning("Allowed Schedulers: {}".format(
            schedulers.ASYNC_IO
        ))
        raise Exception("Invalid Scheduler '{}'".format(scheduler))

"""Factory to create asynchronous tls clients based on asyncio."""
import logging
import asyncio

from pymodbus.client.asynchronous import schedulers
from pymodbus.client.asynchronous.async_io import init_tls_client
from pymodbus.constants import Defaults

_logger = logging.getLogger(__name__)


def async_io_factory(
    host="127.0.0.1",
    port=Defaults.TLSPort,
    sslctx=None,
    server_hostname=None,
    framer=None,
    **kwargs,
):
    """Create asyncio based asynchronous tls clients.

    :param host: Target server"s name, also matched for certificate
    :param port: Port
    :param sslctx: The SSLContext to use for TLS (default None and auto create)
    :param certfile: The optional client"s cert file path for TLS server request
    :param keyfile: The optional client"s key file path for TLS server request
    :param password: The password for for decrypting client"s private key file
    :param framer: Modbus Framer
    :param source_address: Bind address
    :param timeout: Timeout in seconds
    :param kwargs:
    :return: asyncio event loop and tcp client
    """
    try:
        loop = kwargs.pop("loop", None) or asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()

    proto_cls = kwargs.pop("proto_cls", None)
    if not loop.is_running():
        asyncio.set_event_loop(loop)
        cor = init_tls_client(
            proto_cls, loop, host, port, sslctx, server_hostname, framer, **kwargs
        )
        client = loop.run_until_complete(asyncio.gather(cor))[0]
    elif loop is asyncio.get_event_loop():
        return loop, init_tls_client(
            proto_cls, loop, host, port, sslctx, server_hostname, framer, **kwargs
        )
    else:
        cor = init_tls_client(
            proto_cls, loop, host, port, sslctx, server_hostname, framer, **kwargs
        )
        future = asyncio.run_coroutine_threadsafe(cor, loop=loop)
        client = future.result()

    return loop, client


def get_factory(scheduler):
    """Get protocol factory based on the backend scheduler being used.

    :param scheduler: ASYNC_IO
    :return
    """
    if scheduler == schedulers.ASYNC_IO:
        return async_io_factory

    txt = f"Allowed Schedulers: {schedulers.ASYNC_IO}"
    _logger.warning(txt)
    txt = f'Invalid Scheduler "{scheduler}"'
    raise Exception(txt)  # NOSONAR

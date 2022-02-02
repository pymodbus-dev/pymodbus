from __future__ import unicode_literals
from __future__ import absolute_import

import logging
from pymodbus.client.asynchronous.factory.tls import get_factory
from pymodbus.constants import Defaults
from pymodbus.factory import ClientDecoder
from pymodbus.transaction import ModbusTlsFramer

logger = logging.getLogger(__name__)


class AsyncModbusTLSClient(object):
    """
    Actual Async TLS Client to be used.

    To use do::

        from pymodbus.client.asynchronous.tls import AsyncModbusTLSClient
    """
    def __new__(cls, scheduler, host="127.0.0.1", port=Defaults.TLSPort,
                framer=None, sslctx=None, server_hostname=None,
                source_address=None, timeout=None, **kwargs):
        """
        Scheduler to use:
            - async_io (asyncio)
        :param scheduler: Backend to use
        :param host: Host IP address
        :param port: Port
        :param framer: Modbus Framer to use
        :param sslctx: The SSLContext to use for TLS (default None and auto create)
        :param server_hostname: Target server's name matched for certificate
        :param source_address: source address specific to underlying backend
        :param timeout: Time out in seconds
        :param kwargs: Other extra args specific to Backend being used
        :return:
        """
        framer = framer or ModbusTlsFramer(ClientDecoder())
        factory_class = get_factory(scheduler)
        yieldable = factory_class(host=host, port=port, sslctx=sslctx,
                                  server_hostname=server_hostname,
                                  framer=framer, source_address=source_address,
                                  timeout=timeout, **kwargs)
        return yieldable


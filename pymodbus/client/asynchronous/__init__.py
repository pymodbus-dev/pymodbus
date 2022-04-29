"""
Async Modbus Client implementation based on Twisted, tornado and asyncio
------------------------------------------------------------------------

Example run::

    from pymodbus.client.asynchronous import schedulers

    # Import The clients

    from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient as Client
    from pymodbus.client.asynchronous.serial import AsyncModbusSerialClient as Client
    from pymodbus.client.asynchronous.udp import AsyncModbusUDPClient as Client

    # For tornado based asynchronous client use
    event_loop, future = Client(schedulers.IO_LOOP, port=5020)

    # For twisted based asynchronous client use
    event_loop, future = Client(schedulers.REACTOR, port=5020)

    # For asyncio based asynchronous client use
    event_loop, client = Client(schedulers.ASYNC_IO, port=5020)

    # Here event_loop is a thread which would control the backend and future is
    # a Future/deffered object which would be used to
    # add call backs to run asynchronously.

    # The Actual client could be accessed with future.result() with Tornado
    # and future.result when using twisted

    # For asyncio the actual client is returned and event loop is asyncio loop

"""
from pymodbus.compat import is_installed

installed = is_installed('twisted')
if installed:
    # Import deprecated async client only if twisted is installed #338
    from pymodbus.client.asynchronous.deprecated.asynchronous import *
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("Importing deprecated clients. "
                   "Dependency Twisted is Installed")

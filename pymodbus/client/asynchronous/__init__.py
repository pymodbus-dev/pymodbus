"""Async Modbus Client implementation based on Twisted, tornado and asyncio

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
    # a Future/deferred object which would be used to
    # add call backs to run asynchronously.

    # The Actual client could be accessed with future.result() with Tornado
    # and future.result when using twisted

    # For asyncio the actual client is returned and event loop is asyncio loop
"""
import logging
import importlib.util


_logger = logging.getLogger(__name__)

if installed := importlib.util.find_spec("twisted"):
    # Import deprecated async client only if twisted is installed #338
    from pymodbus.client.asynchronous.deprecated.asynchronous import *  # noqa: F401,F403

    _logger.warning("Importing deprecated clients. Dependency Twisted is Installed")

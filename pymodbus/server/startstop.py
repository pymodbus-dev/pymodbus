"""Implementation of a Threaded Modbus Server."""
from __future__ import annotations

import asyncio
import os
from contextlib import suppress

from pymodbus.framer import FramerType
from pymodbus.logging import Log

from .server import (
    ModbusSerialServer,
    ModbusTcpServer,
    ModbusTlsServer,
    ModbusUdpServer,
)


class _serverList:
    """Maintains information about the active server.

    :meta private:
    """

    active_server: ModbusTcpServer | ModbusUdpServer | ModbusSerialServer

    def __init__(self, server):
        """Register new server."""
        self.server = server
        self.loop = asyncio.get_event_loop()

    @classmethod
    async def run(cls, server, custom_functions) -> None:
        """Help starting/stopping server."""
        for func in custom_functions:
            server.decoder.register(func)
        cls.active_server = _serverList(server)  # type: ignore[assignment]
        with suppress(asyncio.exceptions.CancelledError):
            await server.serve_forever()

    @classmethod
    async def async_stop(cls) -> None:
        """Wait for server stop."""
        if not cls.active_server:
            raise RuntimeError("ServerAsyncStop called without server task active.")
        await cls.active_server.server.shutdown()  # type: ignore[union-attr]
        cls.active_server = None  # type: ignore[assignment]

    @classmethod
    def stop(cls):
        """Wait for server stop."""
        if not cls.active_server:
            Log.info("ServerStop called without server task active.")
            return
        if not cls.active_server.loop.is_running():
            Log.info("ServerStop called with loop stopped.")
            return
        future = asyncio.run_coroutine_threadsafe(cls.async_stop(), cls.active_server.loop)
        future.result(timeout=10 if os.name == 'nt' else 0.1)


async def StartAsyncTcpServer(  # pylint: disable=invalid-name,dangerous-default-value
    context,
    custom_functions=[],
    **kwargs,
):
    """Start and run a tcp modbus server.

    For parameter explanation see ModbusTcpServer.

    parameter custom_functions: optional list of custom function classes.
    """
    kwargs.pop("host", None)
    server = ModbusTcpServer(
        context,
        framer=kwargs.pop("framer", FramerType.SOCKET),
        **kwargs
    )
    await _serverList.run(server, custom_functions)


async def StartAsyncTlsServer(  # pylint: disable=invalid-name,dangerous-default-value
    context=None,
    custom_functions=[],
    **kwargs,
):
    """Start and run a tls modbus server.

    For parameter explanation see ModbusTlsServer.

    parameter custom_functions: optional list of custom function classes.
    """
    kwargs.pop("host", None)
    server = ModbusTlsServer(
        context,
        framer=kwargs.pop("framer", FramerType.TLS),
        **kwargs,
    )
    await _serverList.run(server, custom_functions)


async def StartAsyncUdpServer(  # pylint: disable=invalid-name,dangerous-default-value
    context=None,
    custom_functions=[],
    **kwargs,
):
    """Start and run a udp modbus server.

    For parameter explanation see ModbusUdpServer.

    parameter custom_functions: optional list of custom function classes.
    """
    kwargs.pop("host", None)
    server = ModbusUdpServer(
        context,
        **kwargs
    )
    await _serverList.run(server, custom_functions)


async def StartAsyncSerialServer(  # pylint: disable=invalid-name,dangerous-default-value
    context=None,
    custom_functions=[],
    **kwargs,
):
    """Start and run a serial modbus server.

    For parameter explanation see ModbusSerialServer.

    parameter custom_functions: optional list of custom function classes.
    """
    server = ModbusSerialServer(
        context,
        **kwargs
    )
    await _serverList.run(server, custom_functions)


def StartSerialServer(**kwargs):  # pylint: disable=invalid-name
    """Start and run a modbus serial server.

    For parameter explanation see ModbusSerialServer.
    """
    return asyncio.run(StartAsyncSerialServer(**kwargs))


def StartTcpServer(**kwargs):  # pylint: disable=invalid-name
    """Start and run a modbus TCP server.

    For parameter explanation see ModbusTcpServer.
    """
    return asyncio.run(StartAsyncTcpServer(**kwargs))


def StartTlsServer(**kwargs):  # pylint: disable=invalid-name
    """Start and run a modbus TLS server.

    For parameter explanation see ModbusTlsServer.
    """
    return asyncio.run(StartAsyncTlsServer(**kwargs))


def StartUdpServer(**kwargs):  # pylint: disable=invalid-name
    """Start and run a modbus UDP server.

    For parameter explanation see ModbusUdpServer.
    """
    return asyncio.run(StartAsyncUdpServer(**kwargs))


async def ServerAsyncStop():  # pylint: disable=invalid-name
    """Terminate server."""
    await _serverList.async_stop()


def ServerStop():  # pylint: disable=invalid-name
    """Terminate server."""
    _serverList.stop()

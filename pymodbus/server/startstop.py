"""Implementation of a Threaded Modbus Server."""
from __future__ import annotations

import asyncio
import os
from contextlib import suppress

from pymodbus.datastore import ModbusServerContext

from .base import ModbusBaseServer
from .server import (
    ModbusSerialServer,
    ModbusTcpServer,
    ModbusTlsServer,
    ModbusUdpServer,
)


async def StartAsyncTcpServer(  # pylint: disable=invalid-name
    context: ModbusServerContext,
    **kwargs,
) -> None:
    """Start and run a tcp modbus server.

    For parameter explanation see ModbusTcpServer.
    """
    server = ModbusTcpServer(context, **kwargs)
    with suppress(asyncio.exceptions.CancelledError):
        await server.serve_forever()


def StartTcpServer(  # pylint: disable=invalid-name
    context: ModbusServerContext,
    **kwargs
) -> None:
    """Start and run a modbus TCP server.

    For parameter explanation see ModbusTcpServer.
    """
    return asyncio.run(StartAsyncTcpServer(context, **kwargs))


async def StartAsyncTlsServer(  # pylint: disable=invalid-name
    context: ModbusServerContext,
    **kwargs,
) -> None:
    """Start and run a tls modbus server.

    For parameter explanation see ModbusTlsServer.
    """
    server = ModbusTlsServer(context, **kwargs)
    with suppress(asyncio.exceptions.CancelledError):
        await server.serve_forever()


def StartTlsServer(  # pylint: disable=invalid-name
    context: ModbusServerContext,
    **kwargs
) -> None:
    """Start and run a modbus TLS server.

    For parameter explanation see ModbusTlsServer.
    """
    asyncio.run(StartAsyncTlsServer(context, **kwargs))


async def StartAsyncUdpServer(  # pylint: disable=invalid-name
    context: ModbusServerContext,
    **kwargs,
) -> None:
    """Start and run a udp modbus server.

    For parameter explanation see ModbusUdpServer.
    """
    server = ModbusUdpServer(context, **kwargs)
    with suppress(asyncio.exceptions.CancelledError):
        await server.serve_forever()


def StartUdpServer(  # pylint: disable=invalid-name
    context: ModbusServerContext,
    **kwargs
) -> None:
    """Start and run a modbus UDP server.

    For parameter explanation see ModbusUdpServer.
    """
    asyncio.run(StartAsyncUdpServer(context, **kwargs))


async def StartAsyncSerialServer(  # pylint: disable=invalid-name
    context: ModbusServerContext,
    **kwargs,
) -> None:
    """Start and run a serial modbus server.

    For parameter explanation see ModbusSerialServer.
    """
    server = ModbusSerialServer(context, **kwargs)
    with suppress(asyncio.exceptions.CancelledError):
        await server.serve_forever()


def StartSerialServer(  # pylint: disable=invalid-name
    context: ModbusServerContext,
    **kwargs
) -> None:
    """Start and run a modbus serial server.

    For parameter explanation see ModbusSerialServer.
    """
    asyncio.run(StartAsyncSerialServer(context, **kwargs))


async def ServerAsyncStop() -> None:  # pylint: disable=invalid-name
    """Terminate server."""
    if not ModbusBaseServer.active_server:
        raise RuntimeError("Modbus server not running.")
    await ModbusBaseServer.active_server.shutdown()
    ModbusBaseServer.active_server = None


def ServerStop() -> None:  # pylint: disable=invalid-name
    """Terminate server."""
    if not ModbusBaseServer.active_server:
        raise RuntimeError("Modbus server not running.")
    future = asyncio.run_coroutine_threadsafe(ServerAsyncStop(), ModbusBaseServer.active_server.loop)
    future.result(timeout=10 if os.name == 'nt' else 0.1)

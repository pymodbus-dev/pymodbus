"""Implementation of a Threaded Modbus Server."""
from __future__ import annotations

import asyncio
import os

from pymodbus.datastore import ModbusServerContext
from pymodbus.pdu import ModbusPDU

from .base import ModbusBaseServer
from .server import (
    ModbusSerialServer,
    ModbusTcpServer,
    ModbusTlsServer,
    ModbusUdpServer,
)


async def StartAsyncTcpServer(
    context: ModbusServerContext,
    custom_functions: list[type[ModbusPDU]] | None = None,
    **kwargs,
) -> None:
    """Start and run a tcp modbus server.

    :parameter context: Datastore object
    :parameter custom_functions: optional list of custom PDU objects
    :parameter kwargs: for parameter explanation see ModbusTcpServer

    .. tip::
        Only handles a single server !

        Use ModbusTcpServer to allow multiple servers in one app.
    """
    await ModbusTcpServer(context, custom_pdu=custom_functions, **kwargs).serve_forever()


def StartTcpServer(
    context: ModbusServerContext,
    custom_functions: list[type[ModbusPDU]] | None = None,
    **kwargs
) -> None:
    """Start and run a modbus TCP server.

    :parameter context: Datastore object
    :parameter custom_functions: optional list of custom PDU objects
    :parameter kwargs: for parameter explanation see ModbusTcpServer

    .. tip::
        Only handles a single server !

        Use ModbusTcpServer to allow multiple servers in one app.
    """
    asyncio.run(StartAsyncTcpServer(context, custom_functions=custom_functions, **kwargs))


async def StartAsyncTlsServer(
    context: ModbusServerContext,
    custom_functions: list[type[ModbusPDU]] | None = None,
    **kwargs,
) -> None:
    """Start and run a tls modbus server.

    :parameter context: Datastore object
    :parameter custom_functions: optional list of custom PDU objects
    :parameter kwargs: for parameter explanation see ModbusTlsServer

    .. tip::
        Only handles a single server !

        Use ModbusTlsServer to allow multiple servers in one app.
    """
    await ModbusTlsServer(context, custom_pdu=custom_functions, **kwargs).serve_forever()


def StartTlsServer(
    context: ModbusServerContext,
    custom_functions: list[type[ModbusPDU]] | None = None,
    **kwargs
) -> None:
    """Start and run a modbus TLS server.

    :parameter context: Datastore object
    :parameter custom_functions: optional list of custom PDU objects
    :parameter kwargs: for parameter explanation see ModbusTlsServer

    .. tip::
        Only handles a single server !

        Use ModbusTlsServer to allow multiple servers in one app.
    """
    asyncio.run(StartAsyncTlsServer(context, custom_functions=custom_functions, **kwargs))


async def StartAsyncUdpServer(
    context: ModbusServerContext,
    custom_functions: list[type[ModbusPDU]] | None = None,
    **kwargs,
) -> None:
    """Start and run a udp modbus server.

    :parameter context: Datastore object
    :parameter custom_functions: optional list of custom PDU objects
    :parameter kwargs: for parameter explanation see ModbusUdpServer

    .. tip::
        Only handles a single server !

        Use ModbusUdpServer to allow multiple servers in one app.
    """
    await ModbusUdpServer(context, custom_pdu=custom_functions, **kwargs).serve_forever()


def StartUdpServer(
    context: ModbusServerContext,
    custom_functions: list[type[ModbusPDU]] | None = None,
    **kwargs
) -> None:
    """Start and run a modbus UDP server.

    :parameter context: Datastore object
    :parameter custom_functions: optional list of custom PDU objects
    :parameter kwargs: for parameter explanation see ModbusUdpServer

    .. tip::
        Only handles a single server !

        Use ModbusUdpServer to allow multiple servers in one app.
    """
    asyncio.run(StartAsyncUdpServer(context, custom_functions=custom_functions, **kwargs))


async def StartAsyncSerialServer(
    context: ModbusServerContext,
    custom_functions: list[type[ModbusPDU]] | None = None,
    **kwargs,
) -> None:
    """Start and run a serial modbus server.

    :parameter context: Datastore object
    :parameter custom_functions: optional list of custom PDU objects
    :parameter kwargs: for parameter explanation see ModbusSerialServer

    .. tip::
        Only handles a single server !

        Use ModbusSerialServer to allow multiple servers in one app.
    """
    await ModbusSerialServer(context, custom_pdu=custom_functions, **kwargs).serve_forever()


def StartSerialServer(
    context: ModbusServerContext,
    custom_functions: list[type[ModbusPDU]] | None = None,
    **kwargs
) -> None:
    """Start and run a modbus serial server.

    :parameter context: Datastore object
    :parameter custom_functions: optional list of custom PDU objects
    :parameter kwargs: for parameter explanation see ModbusSerialServer

    .. tip::
        Only handles a single server !

        Use ModbusSerialServer to allow multiple servers in one app.
    """
    asyncio.run(StartAsyncSerialServer(context, custom_functions=custom_functions, **kwargs))


async def ServerAsyncStop() -> None:
    """Terminate server."""
    if not ModbusBaseServer.active_server:
        raise RuntimeError("Modbus server not running.")
    await ModbusBaseServer.active_server.shutdown()
    ModbusBaseServer.active_server = None


def ServerStop() -> None:
    """Terminate server."""
    if not ModbusBaseServer.active_server:
        raise RuntimeError("Modbus server not running.")
    future = asyncio.run_coroutine_threadsafe(ServerAsyncStop(), ModbusBaseServer.active_server.loop)
    future.result(timeout=10 if os.name == 'nt' else 0.1)

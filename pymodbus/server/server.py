"""Implementation of a Threaded Modbus Server."""
from __future__ import annotations

import asyncio
import os
from collections.abc import Callable
from contextlib import suppress

from pymodbus.datastore import ModbusServerContext
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.framer import FramerType
from pymodbus.logging import Log
from pymodbus.pdu import ModbusPDU
from pymodbus.transport import CommParams, CommType

from .base import ModbusBaseServer


class ModbusTcpServer(ModbusBaseServer):
    """A modbus threaded tcp socket server.

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        context: ModbusServerContext,
        *,
        framer=FramerType.SOCKET,
        identity: ModbusDeviceIdentification | None = None,
        address: tuple[str, int] = ("", 502),
        ignore_missing_slaves: bool = False,
        broadcast_enable: bool = False,
        trace_packet: Callable[[bool, bytes], bytes] | None = None,
        trace_pdu: Callable[[bool, ModbusPDU], ModbusPDU] | None = None,
        trace_connect: Callable[[bool], None] | None = None,
        custom_pdu: list[type[ModbusPDU]] | None = None,
    ):
        """Initialize the socket server.

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure
        :param address: An optional (interface, port) to bind to.
        :param ignore_missing_slaves: True to not send errors on a request
                        to a missing slave
        :param broadcast_enable: True to treat dev_id 0 as broadcast address,
                        False to treat 0 as any other dev_id
        :param trace_packet: Called with bytestream received/to be sent
        :param trace_pdu: Called with PDU received/to be sent
        :param trace_connect: Called when connected/disconnected
        :param custom_pdu: list of ModbusPDU custom classes
        """
        params = getattr(
            self,
            "tls_setup",
            CommParams(
                comm_type=CommType.TCP,
                comm_name="server_listener",
                reconnect_delay=0.0,
                reconnect_delay_max=0.0,
                timeout_connect=0.0,
            ),
        )
        params.source_address = address
        super().__init__(
            params,
            context,
            ignore_missing_slaves,
            broadcast_enable,
            identity,
            framer,
            trace_packet,
            trace_pdu,
            trace_connect,
            custom_pdu,
        )


class ModbusTlsServer(ModbusTcpServer):
    """A modbus threaded tls socket server.

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        context: ModbusServerContext,
        *,
        framer=FramerType.TLS,
        identity: ModbusDeviceIdentification | None = None,
        address: tuple[str, int] = ("", 502),
        sslctx=None,
        certfile=None,
        keyfile=None,
        password=None,
        ignore_missing_slaves=False,
        broadcast_enable=False,
        trace_packet: Callable[[bool, bytes], bytes] | None = None,
        trace_pdu: Callable[[bool, ModbusPDU], ModbusPDU] | None = None,
        trace_connect: Callable[[bool], None] | None = None,
        custom_pdu: list[type[ModbusPDU]] | None = None,
    ):
        """Overloaded initializer for the socket server.

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure
        :param address: An optional (interface, port) to bind to.
        :param sslctx: The SSLContext to use for TLS (default None and auto
                       create)
        :param certfile: The cert file path for TLS (used if sslctx is None)
        :param keyfile: The key file path for TLS (used if sslctx is None)
        :param password: The password for for decrypting the private key file
        :param ignore_missing_slaves: True to not send errors on a request
                        to a missing slave
        :param broadcast_enable: True to treat dev_id 0 as broadcast address,
                        False to treat 0 as any other dev_id
        :param trace_packet: Called with bytestream received/to be sent
        :param trace_pdu: Called with PDU received/to be sent
        :param trace_connect: Called when connected/disconnected
        :param custom_pdu: list of ModbusPDU custom classes
        """
        self.tls_setup = CommParams(
            comm_type=CommType.TLS,
            comm_name="server_listener",
            reconnect_delay=0.0,
            reconnect_delay_max=0.0,
            timeout_connect=0.0,
            sslctx=CommParams.generate_ssl(
                True, certfile, keyfile, password, sslctx=sslctx
            ),
        )
        super().__init__(
            context,
            framer=framer,
            identity=identity,
            address=address,
            ignore_missing_slaves=ignore_missing_slaves,
            broadcast_enable=broadcast_enable,
            trace_packet=trace_packet,
            trace_pdu=trace_pdu,
            trace_connect=trace_connect,
            custom_pdu=custom_pdu,
        )


class ModbusUdpServer(ModbusBaseServer):
    """A modbus threaded udp socket server.

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        context: ModbusServerContext,
        *,
        framer=FramerType.SOCKET,
        identity: ModbusDeviceIdentification | None = None,
        address: tuple[str, int] = ("", 502),
        ignore_missing_slaves: bool = False,
        broadcast_enable: bool = False,
        trace_packet: Callable[[bool, bytes], bytes] | None = None,
        trace_pdu: Callable[[bool, ModbusPDU], ModbusPDU] | None = None,
        trace_connect: Callable[[bool], None] | None = None,
        custom_pdu: list[type[ModbusPDU]] | None = None,
    ):
        """Overloaded initializer for the socket server.

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure
        :param address: An optional (interface, port) to bind to.
        :param ignore_missing_slaves: True to not send errors on a request
                            to a missing slave
        :param broadcast_enable: True to treat dev_id 0 as broadcast address,
                            False to treat 0 as any other dev_id
        :param trace_packet: Called with bytestream received/to be sent
        :param trace_pdu: Called with PDU received/to be sent
        :param trace_connect: Called when connected/disconnected
        :param custom_pdu: list of ModbusPDU custom classes
        """
        # ----------------
        params = CommParams(
            comm_type=CommType.UDP,
            comm_name="server_listener",
            source_address=address,
            reconnect_delay=0.0,
            reconnect_delay_max=0.0,
            timeout_connect=0.0,
        )
        super().__init__(
            params,
            context,
            ignore_missing_slaves,
            broadcast_enable,
            identity,
            framer,
            trace_packet,
            trace_pdu,
            trace_connect,
            custom_pdu,
        )


class ModbusSerialServer(ModbusBaseServer):
    """A modbus threaded serial socket server.

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    def __init__(
        self,
        context: ModbusServerContext,
        *,
        framer: FramerType = FramerType.RTU,
        ignore_missing_slaves: bool = False,
        identity: ModbusDeviceIdentification | None = None,
        broadcast_enable: bool = False,
        trace_packet: Callable[[bool, bytes], bytes] | None = None,
        trace_pdu: Callable[[bool, ModbusPDU], ModbusPDU] | None = None,
        trace_connect: Callable[[bool], None] | None = None,
        custom_pdu: list[type[ModbusPDU]] | None = None,
        **kwargs
    ):
        """Initialize the socket server.

        If the identity structure is not passed in, the ModbusControlBlock
        uses its own empty structure.
        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use, default FramerType.RTU
        :param identity: An optional identify structure
        :param port: The serial port to attach to
        :param stopbits: The number of stop bits to use
        :param bytesize: The bytesize of the serial messages
        :param parity: Which kind of parity to use
        :param baudrate: The baud rate to use for the serial device
        :param timeout: The timeout to use for the serial device
        :param handle_local_echo: (optional) Discard local echo from dongle.
        :param ignore_missing_slaves: True to not send errors on a request
                            to a missing slave
        :param broadcast_enable: True to treat dev_id 0 as broadcast address,
                            False to treat 0 as any other dev_id
        :param reconnect_delay: reconnect delay in seconds
        :param trace_packet: Called with bytestream received/to be sent
        :param trace_pdu: Called with PDU received/to be sent
        :param trace_connect: Called when connected/disconnected
        :param custom_pdu: list of ModbusPDU custom classes
        """
        params = CommParams(
            comm_type=CommType.SERIAL,
            comm_name="server_listener",
            reconnect_delay=kwargs.get("reconnect_delay", 2),
            reconnect_delay_max=0.0,
            timeout_connect=kwargs.get("timeout", 3),
            source_address=(kwargs.get("port", 0), 0),
            bytesize=kwargs.get("bytesize", 8),
            parity=kwargs.get("parity", "N"),
            baudrate=kwargs.get("baudrate", 19200),
            stopbits=kwargs.get("stopbits", 1),
            handle_local_echo=kwargs.get("handle_local_echo", False)
        )
        super().__init__(
            params,
            context,
            ignore_missing_slaves,
            broadcast_enable,
            identity,
            framer,
            trace_packet,
            trace_pdu,
            trace_connect,
            custom_pdu,
        )
        self.handle_local_echo = kwargs.get("handle_local_echo", False)


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

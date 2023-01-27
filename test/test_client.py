"""Test client sync."""
import asyncio
import socket
import ssl
from test.conftest import return_as_coroutine, run_coroutine
from unittest import mock

import pytest

import pymodbus.bit_read_message as pdu_bit_read
import pymodbus.bit_write_message as pdu_bit_write
import pymodbus.client as lib_client
import pymodbus.diag_message as pdu_diag
import pymodbus.other_message as pdu_other_msg
import pymodbus.register_read_message as pdu_reg_read
import pymodbus.register_write_message as pdu_req_write
from pymodbus.client.base import ModbusBaseClient, ModbusClientProtocol
from pymodbus.client.mixin import ModbusClientMixin
from pymodbus.constants import Defaults
from pymodbus.exceptions import ConnectionException, NotImplementedException
from pymodbus.framer.ascii_framer import ModbusAsciiFramer
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.framer.socket_framer import ModbusSocketFramer
from pymodbus.framer.tls_framer import ModbusTlsFramer


@pytest.mark.parametrize(
    "arglist",
    [
        [
            {},
            {"address": 0x01},
            {"address": 0x01, "value": False},
            {"msg": "long message"},
            {"toggle": False},
            {"address": 0x01, "values": [False, True]},
            {"address": 0x01, "values": [22, 44]},
        ]
    ],
)
@pytest.mark.parametrize(
    "method, arg, response",
    [
        ("read_coils", 1, pdu_bit_read.ReadCoilsRequest),
        ("read_discrete_inputs", 1, pdu_bit_read.ReadDiscreteInputsRequest),
        ("read_holding_registers", 1, pdu_reg_read.ReadHoldingRegistersRequest),
        ("read_input_registers", 1, pdu_reg_read.ReadInputRegistersRequest),
        ("write_coil", 2, pdu_bit_write.WriteSingleCoilRequest),
        ("write_register", 2, pdu_req_write.WriteSingleRegisterRequest),
        ("read_exception_status", 0, pdu_other_msg.ReadExceptionStatusRequest),
        ("diag_query_data", 3, pdu_diag.ReturnQueryDataRequest),
        ("diag_restart_communication", 4, pdu_diag.RestartCommunicationsOptionRequest),
        ("diag_read_diagnostic_register", 0, pdu_diag.ReturnDiagnosticRegisterRequest),
        (
            "diag_change_ascii_input_delimeter",
            0,
            pdu_diag.ChangeAsciiInputDelimiterRequest,
        ),
        ("diag_force_listen_only", 0, pdu_diag.ForceListenOnlyModeRequest),
        ("diag_clear_counters", 0, pdu_diag.ClearCountersRequest),
        ("diag_read_bus_message_count", 0, pdu_diag.ReturnBusMessageCountRequest),
        (
            "diag_read_bus_comm_error_count",
            0,
            pdu_diag.ReturnBusCommunicationErrorCountRequest,
        ),
        (
            "diag_read_bus_exception_error_count",
            0,
            pdu_diag.ReturnBusExceptionErrorCountRequest,
        ),
        ("diag_read_slave_message_count", 0, pdu_diag.ReturnSlaveMessageCountRequest),
        (
            "diag_read_slave_no_response_count",
            0,
            pdu_diag.ReturnSlaveNoResponseCountRequest,
        ),
        ("diag_read_slave_nak_count", 0, pdu_diag.ReturnSlaveNAKCountRequest),
        ("diag_read_slave_busy_count", 0, pdu_diag.ReturnSlaveBusyCountRequest),
        (
            "diag_read_bus_char_overrun_count",
            0,
            pdu_diag.ReturnSlaveBusCharacterOverrunCountRequest,
        ),
        ("diag_read_iop_overrun_count", 0, pdu_diag.ReturnIopOverrunCountRequest),
        ("diag_clear_overrun_counter", 0, pdu_diag.ClearOverrunCountRequest),
        ("diag_getclear_modbus_response", 0, pdu_diag.GetClearModbusPlusRequest),
        ("write_coils", 5, pdu_bit_write.WriteMultipleCoilsRequest),
        ("write_registers", 6, pdu_req_write.WriteMultipleRegistersRequest),
        ("readwrite_registers", 1, pdu_reg_read.ReadWriteMultipleRegistersRequest),
        ("mask_write_register", 1, pdu_req_write.MaskWriteRegisterRequest),
    ],
)
def test_client_mixin(arglist, method, arg, response):
    """Test mixin responses."""
    rr = getattr(ModbusClientMixin(), method)(**arglist[arg])
    assert isinstance(rr, response)


@pytest.mark.xdist_group(name="client")
@pytest.mark.parametrize(
    "arg_list",
    [
        {
            "fix": {
                "opt_args": {
                    "timeout": Defaults.Timeout + 2,
                    "retries": Defaults.Retries + 2,
                    "retry_on_empty": not Defaults.RetryOnEmpty,
                    "close_comm_on_error": not Defaults.CloseCommOnError,
                    "strict": not Defaults.Strict,
                    "broadcast_enable": not Defaults.BroadcastEnable,
                    "reconnect_delay": 117,
                    "reconnect_delay_max": 250,
                },
                "defaults": {
                    "timeout": Defaults.Timeout,
                    "retries": Defaults.Retries,
                    "retry_on_empty": Defaults.RetryOnEmpty,
                    "close_comm_on_error": Defaults.CloseCommOnError,
                    "strict": Defaults.Strict,
                    "broadcast_enable": Defaults.BroadcastEnable,
                    "reconnect_delay": Defaults.ReconnectDelay,
                    "reconnect_delay_max": Defaults.ReconnectDelayMax,
                },
            },
            "serial": {
                "pos_arg": "/dev/tty",
                "opt_args": {
                    "framer": ModbusAsciiFramer,
                    "baudrate": Defaults.Baudrate + 500,
                    "bytesize": Defaults.Bytesize - 1,
                    "parity": "E",
                    "stopbits": Defaults.Stopbits + 1,
                    "handle_local_echo": not Defaults.HandleLocalEcho,
                },
                "defaults": {
                    "host": None,
                    "port": "/dev/tty",
                    "framer": ModbusRtuFramer,
                    "baudrate": Defaults.Baudrate,
                    "bytesize": Defaults.Bytesize,
                    "parity": Defaults.Parity,
                    "stopbits": Defaults.Stopbits,
                    "handle_local_echo": Defaults.HandleLocalEcho,
                },
            },
            "tcp": {
                "pos_arg": "192.168.1.2",
                "opt_args": {
                    "port": 112,
                    "framer": ModbusAsciiFramer,
                    "source_address": ("195.6.7.8", 1025),
                },
                "defaults": {
                    "host": "192.168.1.2",
                    "port": Defaults.TcpPort,
                    "framer": ModbusSocketFramer,
                    "source_address": None,
                },
            },
            "tls": {
                "pos_arg": "192.168.1.2",
                "opt_args": {
                    "port": 211,
                    "framer": ModbusAsciiFramer,
                    "source_address": ("195.6.7.8", 1025),
                    "sslctx": None,
                    "certfile": None,
                    "keyfile": None,
                    "password": None,
                },
                "defaults": {
                    "host": "192.168.1.2",
                    "port": Defaults.TlsPort,
                    "framer": ModbusTlsFramer,
                    "source_address": None,
                    "sslctx": None,
                    "certfile": None,
                    "keyfile": None,
                    "password": None,
                },
            },
            "udp": {
                "pos_arg": "192.168.1.2",
                "opt_args": {
                    "port": 121,
                    "framer": ModbusAsciiFramer,
                    "source_address": ("195.6.7.8", 1025),
                },
                "defaults": {
                    "host": "192.168.1.2",
                    "port": Defaults.UdpPort,
                    "framer": ModbusSocketFramer,
                    "source_address": None,
                },
            },
        },
    ],
)
@pytest.mark.parametrize(
    "type_args, clientclass",
    [
        # TBD ("serial", lib_client.AsyncModbusSerialClient),
        # TBD ("serial", lib_client.ModbusSerialClient),
        ("tcp", lib_client.AsyncModbusTcpClient),
        ("tcp", lib_client.ModbusTcpClient),
        ("tls", lib_client.AsyncModbusTlsClient),
        ("tls", lib_client.ModbusTlsClient),
        ("udp", lib_client.AsyncModbusUdpClient),
        ("udp", lib_client.ModbusUdpClient),
    ],
)
@pytest.mark.parametrize("test_default", [True, False])
def test_client_instanciate(
    arg_list,
    type_args,
    clientclass,
    test_default,
):
    """Try to instantiate clients."""
    cur_args = arg_list[type_args]
    if test_default:
        client = clientclass(cur_args["pos_arg"])
        to_test = dict(arg_list["fix"]["defaults"], **cur_args["defaults"])
    else:
        client = clientclass(
            cur_args["pos_arg"],
            **arg_list["fix"]["opt_args"],
            **cur_args["opt_args"],
        )
        to_test = dict(arg_list["fix"]["opt_args"], **cur_args["opt_args"])
        to_test["host"] = cur_args["defaults"]["host"]

    for arg, arg_test in to_test.items():
        assert getattr(client.params, arg) == arg_test

    # Test information methods
    client.last_frame_end = 2
    client.silent_interval = 2
    assert client.idle_time() == 4
    client.last_frame_end = None
    assert not client.idle_time()

    initial_delay = client.delay_ms
    assert initial_delay > 0  # nosec
    client.delay_ms *= 2

    assert client.delay_ms > initial_delay
    client.reset_delay()
    assert client.delay_ms == initial_delay

    rc1 = client._get_address_family("127.0.0.1")  # pylint: disable=protected-access
    assert socket.AF_INET == rc1
    rc2 = client._get_address_family("::1")  # pylint: disable=protected-access
    assert socket.AF_INET6 == rc2

    # a successful execute
    client.connect = lambda: True
    client.protocol = lambda: True
    client.transaction = mock.Mock(**{"execute.return_value": True})

    # a unsuccessful connect
    client.connect = lambda: False
    client.protocol = None
    with pytest.raises(ConnectionException):
        client.execute()


def test_client_modbusbaseclient():
    """Test modbus base client class."""
    client = ModbusBaseClient(framer=ModbusAsciiFramer)
    client.register(pdu_bit_read.ReadCoilsResponse)
    buffer = "123ABC"
    assert client.send(buffer) == buffer
    assert client.recv(10) == 10

    with pytest.raises(NotImplementedException):
        client.connect()
    with pytest.raises(NotImplementedException):
        client.is_socket_open()
    with pytest.raises(NotImplementedException):
        client.close()

    with mock.patch(
        "pymodbus.client.base.ModbusBaseClient.connect"
    ) as p_connect, mock.patch(
        "pymodbus.client.base.ModbusBaseClient.close"
    ) as p_close:

        p_connect.return_value = True
        p_close.return_value = True
        with ModbusBaseClient(framer=ModbusAsciiFramer) as b_client:
            str(b_client)
        p_connect.return_value = False


async def test_client_made_connection():
    """Test factory protocol made connection."""
    mock_protocol_class = mock.MagicMock()
    client = lib_client.AsyncModbusTcpClient(
        "127.0.0.1", protocol_class=mock_protocol_class
    )
    assert not client.connected
    assert client.protocol is None
    client.protocol_made_connection(mock.sentinel.PROTOCOL)
    assert client.connected
    assert client.protocol is mock.sentinel.PROTOCOL

    client.protocol_made_connection(mock.sentinel.PROTOCOL_UNEXPECTED)
    assert client.connected
    assert client.protocol is mock.sentinel.PROTOCOL


async def test_client_lost_connection():
    """Test factory protocol lost connection."""
    mock_protocol_class = mock.MagicMock()
    client = lib_client.AsyncModbusTcpClient(
        "127.0.0.1", protocol_class=mock_protocol_class
    )
    assert not client.connected
    assert client.protocol is None

    # fake client is connected and *then* looses connection:
    client.connected = True
    client.params.host = mock.sentinel.HOST
    client.params.port = mock.sentinel.PORT
    client.protocol = mock.sentinel.PROTOCOL
    client.protocol_lost_connection(mock.sentinel.PROTOCOL_UNEXPECTED)
    assert not client.connected

    client.connected = True
    with mock.patch(
        "pymodbus.client.tcp.AsyncModbusTcpClient._reconnect"
    ) as mock_reconnect:
        mock_reconnect.return_value = mock.sentinel.RECONNECT_GENERATOR

        client.protocol_lost_connection(mock.sentinel.PROTOCOL)
    assert not client.connected
    assert client.protocol is None


async def test_client_base_async():
    """Test modbus base client class."""
    with mock.patch(
        "pymodbus.client.base.ModbusBaseClient.connect"
    ) as p_connect, mock.patch(
        "pymodbus.client.base.ModbusBaseClient.close"
    ) as p_close:

        loop = asyncio.get_event_loop()
        p_connect.return_value = loop.create_future()
        p_connect.return_value.set_result(True)
        p_close.return_value = loop.create_future()
        p_close.return_value.set_result(True)
        async with ModbusBaseClient(framer=ModbusAsciiFramer) as client:
            str(client)
        p_connect.return_value = loop.create_future()
        p_connect.return_value.set_result(False)
        p_close.return_value = loop.create_future()
        p_close.return_value.set_result(False)


@pytest.mark.skip
async def test_client_protocol():
    """Test base modbus async client protocol."""
    protocol = ModbusClientProtocol(framer=ModbusSocketFramer)
    assert protocol.factory is None
    assert protocol.transport is None
    assert not protocol.connected

    protocol.factory = mock.MagicMock()
    protocol.connection_made(mock.sentinel.TRANSPORT)
    assert protocol.transport is mock.sentinel.TRANSPORT
    protocol.factory.protocol_made_connection.assert_called_once_with(  # pylint: disable=no-member
        protocol
    )
    assert (
        not protocol.factory.protocol_lost_connection.call_count  # nosec pylint: disable=no-member
    )

    protocol.factory.reset_mock()
    protocol.connection_lost(mock.sentinel.REASON)
    assert protocol.transport is None  # nosec
    assert (
        not protocol.factory.protocol_made_connection.call_count  # nosec pylint: disable=no-member
    )
    protocol.factory.protocol_lost_connection.assert_called_once_with(  # pylint: disable=no-member
        protocol
    )
    protocol.raise_future = mock.MagicMock()
    request = mock.MagicMock()
    protocol.transaction.addTransaction(request, 1)
    protocol.connection_lost(mock.sentinel.REASON)
    protocol.raise_future.assert_called_once()
    call_args = protocol.raise_future.call_args.args
    assert call_args[0] == request
    assert isinstance(call_args[1], ConnectionException)
    protocol.transport = mock.MagicMock()
    protocol.transport = None
    await protocol.close()


async def test_client_protocol_receiver():
    """Test the client protocol data received"""
    protocol = ModbusClientProtocol(framer=ModbusSocketFramer)
    transport = mock.MagicMock()
    protocol.connection_made(transport)
    assert protocol.transport == transport
    assert protocol.connected
    data = b"\x00\x00\x12\x34\x00\x06\xff\x01\x01\x02\x00\x04"

    # setup existing request
    assert not list(protocol.transaction)
    response = protocol._build_response(0x00)  # pylint: disable=protected-access
    protocol.data_received(data)
    result = response.result()
    assert isinstance(result, pdu_bit_read.ReadCoilsResponse)

    protocol._connected = False  # pylint: disable=protected-access
    with pytest.raises(ConnectionException):
        await protocol._build_response(0x00)  # pylint: disable=protected-access


async def test_client_protocol_response():
    """Test the udp client protocol builds responses"""
    protocol = ModbusClientProtocol(framer=ModbusSocketFramer)
    response = protocol._build_response(0x00)  # pylint: disable=protected-access
    excp = response.exception()
    assert isinstance(excp, ConnectionException)
    assert not list(protocol.transaction)

    protocol._connected = True  # pylint: disable=protected-access
    protocol._build_response(0x00)  # pylint: disable=protected-access
    assert len(list(protocol.transaction)) == 1


async def test_client_protocol_handler():
    """Test the client protocol handles responses"""
    protocol = ModbusClientProtocol(framer=ModbusSocketFramer)
    transport = mock.MagicMock()
    protocol.connection_made(transport=transport)
    reply = pdu_bit_read.ReadCoilsRequest(1, 1)
    reply.transaction_id = 0x00
    protocol._handle_response(None)  # pylint: disable=protected-access
    protocol._handle_response(reply)  # pylint: disable=protected-access
    response = protocol._build_response(0x00)  # pylint: disable=protected-access
    protocol._handle_response(reply)  # pylint: disable=protected-access
    result = response.result()
    assert result == reply


async def test_client_protocol_execute():
    """Test the client protocol execute method"""
    protocol = ModbusClientProtocol("127.0.0.1", framer=ModbusSocketFramer)
    protocol.create_future = mock.MagicMock()
    fut = asyncio.Future()
    fut.set_result(fut)
    protocol.create_future.return_value = fut
    transport = mock.MagicMock()
    protocol.connection_made(transport)
    protocol.transport.write = mock.Mock()

    request = pdu_bit_read.ReadCoilsRequest(1, 1)
    response = await protocol.execute(request)
    tid = request.transaction_id
    f_trans = protocol.transaction.getTransaction(tid)
    assert response == f_trans

    protocol.params.broadcast_enable = True
    request = pdu_bit_read.ReadCoilsRequest(1, 1)
    response = await protocol.execute(request)


def test_client_udp():
    """Test client udp."""
    protocol = ModbusClientProtocol("127.0.0.1", framer=ModbusSocketFramer)
    protocol.datagram_received(bytes("00010000", "utf-8"), 1)
    protocol.transport = mock.MagicMock()
    protocol.use_udp = True
    protocol.write_transport(bytes("00010000", "utf-8"))


def test_client_udp_connect():
    """Test the Udp client connection method"""
    with mock.patch.object(socket, "socket") as mock_method:

        class DummySocket:  # pylint: disable=too-few-public-methods
            """Dummy socket."""

            def settimeout(self, *a, **kwa):
                """Set timeout."""

        mock_method.return_value = DummySocket()
        client = lib_client.ModbusUdpClient("127.0.0.1")
        assert client.connect()

    with mock.patch.object(socket, "socket") as mock_method:
        mock_method.side_effect = socket.error()
        client = lib_client.ModbusUdpClient("127.0.0.1")
        assert not client.connect()


def test_client_tcp_connect():
    """Test the tcp client connection method"""
    with mock.patch.object(socket, "create_connection") as mock_method:
        _socket = mock.MagicMock()
        mock_method.return_value = _socket
        client = lib_client.ModbusTcpClient("127.0.0.1")
        _socket.getsockname.return_value = ("dmmy", 1234)
        assert client.connect()

    with mock.patch.object(socket, "create_connection") as mock_method:
        mock_method.side_effect = socket.error()
        client = lib_client.ModbusTcpClient("127.0.0.1")
        assert not client.connect()


def test_client_tls_connect():
    """Test the tls client connection method"""
    with mock.patch.object(ssl.SSLSocket, "connect") as mock_method:
        client = lib_client.ModbusTlsClient("127.0.0.1")
        assert client.connect()

    with mock.patch.object(socket, "create_connection") as mock_method:
        mock_method.side_effect = socket.error()
        client = lib_client.ModbusTlsClient("127.0.0.1")
        assert not client.connect()


@mock.patch("pymodbus.client.tcp.asyncio.sleep")
async def test_client_reconnect(mock_sleep):
    """Test factory reconnect."""
    mock_protocol_class = mock.MagicMock()
    mock_sleep.side_effect = return_as_coroutine()
    loop = asyncio.get_running_loop()
    loop.create_connection = mock.MagicMock(return_value=(None, None))
    client = lib_client.AsyncModbusTcpClient(
        "127.0.0.1", protocol_class=mock_protocol_class
    )

    # set delay long enough so we have only one connection attempt below
    client.params.reconnect_delay = 5000
    await client.connect()

    run_coroutine(client._reconnect())  # pylint: disable=protected-access
    mock_sleep.assert_called_once_with(5)
    assert loop.create_connection.call_count >= 1  # nosec

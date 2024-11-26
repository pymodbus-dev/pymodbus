"""Test client sync."""
import socket
import ssl
from unittest import mock

import pytest

import pymodbus.client as lib_client
import pymodbus.pdu.bit_message as pdu_bit
import pymodbus.pdu.diag_message as pdu_diag
import pymodbus.pdu.file_message as pdu_file_msg
import pymodbus.pdu.mei_message as pdu_mei
import pymodbus.pdu.other_message as pdu_other_msg
import pymodbus.pdu.register_message as pdu_reg
from examples.helper import get_certificate
from pymodbus import FramerType
from pymodbus.client.base import ModbusBaseClient
from pymodbus.client.mixin import ModbusClientMixin
from pymodbus.exceptions import ConnectionException, ModbusException
from pymodbus.pdu import ModbusPDU
from pymodbus.transport import CommParams, CommType
from pymodbus.utilities import ModbusTransactionState


BASE_PORT = 6500

class TestMixin:
    """Test mixin for clients."""

    @pytest.mark.parametrize(
        "arglist",
        [
            [
                {},
                {"address": 0x01},
                {"address": 0x01, "value": False},
                {"msg": b"long message"},
                {"toggle": False},
                {"address": 0x01, "values": [False, True]},
                {"address": 0x01, "values": [22, 44]},
                {"records": (0, 0)},
            ]
        ],
    )
    @pytest.mark.parametrize(
        ("method", "arg", "pdu_request"),
        [
            ("read_coils", 1, pdu_bit.ReadCoilsRequest),
            ("read_discrete_inputs", 1, pdu_bit.ReadDiscreteInputsRequest),
            ("read_holding_registers", 1, pdu_reg.ReadHoldingRegistersRequest),
            ("read_input_registers", 1, pdu_reg.ReadInputRegistersRequest),
            ("write_coil", 2, pdu_bit.WriteSingleCoilRequest),
            ("write_register", 2, pdu_reg.WriteSingleRegisterRequest),
            ("read_exception_status", 0, pdu_other_msg.ReadExceptionStatusRequest),
            ("diag_query_data", 3, pdu_diag.ReturnQueryDataRequest),
            ("diag_restart_communication", 4, pdu_diag.RestartCommunicationsOptionRequest),
            ("diag_read_diagnostic_register", 0, pdu_diag.ReturnDiagnosticRegisterRequest),
            ("diag_change_ascii_input_delimeter", 0, pdu_diag.ChangeAsciiInputDelimiterRequest),
            ("diag_force_listen_only", 0, pdu_diag.ForceListenOnlyModeRequest),
            ("diag_clear_counters", 0, pdu_diag.ClearCountersRequest),
            ("diag_read_bus_message_count", 0, pdu_diag.ReturnBusMessageCountRequest),
            ("diag_read_bus_comm_error_count",0, pdu_diag.ReturnBusCommunicationErrorCountRequest),
            ("diag_read_bus_exception_error_count", 0, pdu_diag.ReturnBusExceptionErrorCountRequest),
            ("diag_read_slave_message_count", 0, pdu_diag.ReturnSlaveMessageCountRequest),
            ("diag_read_slave_no_response_count", 0, pdu_diag.ReturnSlaveNoResponseCountRequest),
            ("diag_read_slave_nak_count", 0, pdu_diag.ReturnSlaveNAKCountRequest),
            ("diag_read_slave_busy_count", 0, pdu_diag.ReturnSlaveBusyCountRequest),
            ("diag_read_bus_char_overrun_count", 0, pdu_diag.ReturnSlaveBusCharacterOverrunCountRequest),
            ("diag_read_iop_overrun_count", 0, pdu_diag.ReturnIopOverrunCountRequest),
            ("diag_clear_overrun_counter", 0, pdu_diag.ClearOverrunCountRequest),
            ("diag_getclear_modbus_response", 0, pdu_diag.GetClearModbusPlusRequest),
            ("diag_get_comm_event_counter", 0, pdu_other_msg.GetCommEventCounterRequest),
            ("diag_get_comm_event_log", 0, pdu_other_msg.GetCommEventLogRequest),
            ("write_coils", 5, pdu_bit.WriteMultipleCoilsRequest),
            ("write_registers", 6, pdu_reg.WriteMultipleRegistersRequest),
            ("readwrite_registers", 0, pdu_reg.ReadWriteMultipleRegistersRequest),
            ("readwrite_registers", 6, pdu_reg.ReadWriteMultipleRegistersRequest),
            ("mask_write_register", 1, pdu_reg.MaskWriteRegisterRequest),
            ("report_slave_id", 0, pdu_other_msg.ReportSlaveIdRequest),
            ("read_file_record", 7, pdu_file_msg.ReadFileRecordRequest),
            ("write_file_record", 7, pdu_file_msg.WriteFileRecordRequest),
            ("read_fifo_queue", 1, pdu_file_msg.ReadFifoQueueRequest),
            ("read_device_information", 0, pdu_mei.ReadDeviceInformationRequest),
        ],
    )
    def test_client_mixin(self, arglist, method, arg, pdu_request):
        """Test mixin responses."""
        pdu_to_call = None

        def fake_execute(_self, _no_response_expected, request):
            """Set PDU request."""
            nonlocal pdu_to_call
            pdu_to_call = request

        with mock.patch.object(ModbusClientMixin, "execute", fake_execute):
            getattr(ModbusClientMixin(), method)(**arglist[arg])
            assert isinstance(pdu_to_call, pdu_request)


    @pytest.mark.parametrize(
        ("datatype", "value", "registers"),
        [
            (ModbusClientMixin.DATATYPE.STRING, "abcd", [0x6162, 0x6364]),
            (ModbusClientMixin.DATATYPE.STRING, "a", [0x6100]),
            (ModbusClientMixin.DATATYPE.UINT16, 27123, [0x69F3]),
            (ModbusClientMixin.DATATYPE.INT16, -27123, [0x960D]),
            (ModbusClientMixin.DATATYPE.UINT32, 27123, [0x0000, 0x69F3]),
            (ModbusClientMixin.DATATYPE.UINT32, 32145678, [0x01EA, 0x810E]),
            (ModbusClientMixin.DATATYPE.INT32, -32145678, [0xFE15, 0x7EF2]),
            (
                ModbusClientMixin.DATATYPE.UINT64,
                1234567890123456789,
                [0x1122, 0x10F4, 0x7DE9, 0x8115],
            ),
            (
                ModbusClientMixin.DATATYPE.INT64,
                -1234567890123456789,
                [0xEEDD, 0xEF0B, 0x8216, 0x7EEB],
            ),
            (ModbusClientMixin.DATATYPE.FLOAT32, 27123.5, [0x46D3, 0xE700]),
            (ModbusClientMixin.DATATYPE.FLOAT32, 3.141592, [0x4049, 0x0FD8]),
            (ModbusClientMixin.DATATYPE.FLOAT32, -3.141592, [0xC049, 0x0FD8]),
            (ModbusClientMixin.DATATYPE.FLOAT64, 27123.5, [0x40DA, 0x7CE0, 0x0000, 0x0000]),
            (
                ModbusClientMixin.DATATYPE.FLOAT64,
                3.14159265358979,
                [0x4009, 0x21FB, 0x5444, 0x2D11],
            ),
            (
                ModbusClientMixin.DATATYPE.FLOAT64,
                -3.14159265358979,
                [0xC009, 0x21FB, 0x5444, 0x2D11],
            ),
        ],
    )
    def test_client_mixin_convert(self, datatype, registers, value):
        """Test converter methods."""
        result = ModbusClientMixin.convert_from_registers(registers, datatype)
        if datatype == ModbusClientMixin.DATATYPE.FLOAT32:
            result = round(result, 6)
        assert result == value
        regs = ModbusClientMixin.convert_to_registers(value, datatype)
        assert regs == registers

    @pytest.mark.parametrize(
        ("datatype", "value", "registers"),
        [
            (ModbusClientMixin.DATATYPE.STRING, "0123", [b'\x30\x31', b'\x32\x33']),
            (ModbusClientMixin.DATATYPE.UINT16, 258, [b'\x01\x02']),
            (ModbusClientMixin.DATATYPE.INT16, -32510, [b'\x81\x02']),
            (ModbusClientMixin.DATATYPE.UINT32, 16909060, [b'\x01\x02', b'\x03\x04']),
            (ModbusClientMixin.DATATYPE.INT32, -2130574588, [b'\x81\x02', b'\x03\x04']),
            (
                ModbusClientMixin.DATATYPE.UINT64,
                72623859790382856,
                [b'\x01\x02', b'\x03\x04', b'\x05\x06', b'\x07\x08'],
            ),
            (
                ModbusClientMixin.DATATYPE.INT64,
                -9150748177064392952,
                [b'\x81\x02', b'\x03\x04', b'\x05\x06', b'\x07\x08'],
            ),
            (ModbusClientMixin.DATATYPE.FLOAT32, 8.125736, [b'\x41\x02', b'\x03\x04']),
            (ModbusClientMixin.DATATYPE.FLOAT64, 147552.502453, [b'\x41\x02', b'\x03\x04', b'\x05\x06', b'\x14\x16']),
        ],
    )
    def test_client_mixin_convert_1234(self, datatype, registers, value):
        """Test converter methods."""
        for i in range(0, len(registers)):
            registers[i] = int.from_bytes(registers[i], "big")
        regs = ModbusClientMixin.convert_to_registers(value, datatype)
        result = ModbusClientMixin.convert_from_registers(regs, datatype)
        if datatype == ModbusClientMixin.DATATYPE.FLOAT32 or datatype == ModbusClientMixin.DATATYPE.FLOAT64:
            result = round(result, 6)
        assert result == value
        assert regs == registers

    def test_client_mixin_convert_fail(self):
        """Test convert fail."""
        with pytest.raises(TypeError):
            ModbusClientMixin.convert_to_registers(123, ModbusClientMixin.DATATYPE.STRING)

        with pytest.raises(ModbusException):
            ModbusClientMixin.convert_from_registers([123], ModbusClientMixin.DATATYPE.FLOAT64)


class TestClientBase:
    """Test client code."""

    @pytest.mark.parametrize(
        "arg_list",
        [
            {
                "fix": {
                    "opt_args": {
                        "timeout": 3 + 2,
                        "retries": 3 + 2,
                        "reconnect_delay": 117,
                        "reconnect_delay_max": 250,
                    },
                    "defaults": {
                        "timeout": 3,
                        "retries": 3,
                        "reconnect_delay": 100,
                        "reconnect_delay_max": 1000 * 60 * 5,
                    },
                },
                "serial": {
                    "pos_arg": "/dev/tty",
                    "opt_args": {
                        "framer": FramerType.ASCII,
                        "baudrate": 19200 + 500,
                        "bytesize": 8 - 1,
                        "parity": "E",
                        "stopbits": 1 + 1,
                        "handle_local_echo": True,
                    },
                    "defaults": {
                        "port": "/dev/tty",
                        "framer": FramerType.RTU,
                        "baudrate": 19200,
                        "bytesize": 8,
                        "parity": "N",
                        "stopbits": 1,
                        "handle_local_echo": False,
                    },
                },
                "tcp": {
                    "pos_arg": "192.168.1.2",
                    "opt_args": {
                        "port": 112,
                        "framer": FramerType.ASCII,
                        "source_address": ("195.6.7.8", 1025),
                    },
                    "defaults": {
                        "port": 502,
                        "framer": FramerType.SOCKET,
                        "source_address": None,
                    },
                },
                "tls": {
                    "pos_arg": "192.168.1.2",
                    "opt_args": {
                        "port": 802,
                        "framer": FramerType.TLS,
                        "source_address": None,
                        "sslctx": None,
                    },
                    "defaults": {
                        "port": 802,
                        "framer": FramerType.TLS,
                        "source_address": None,
                        "sslctx": None,
                    },
                },
                "udp": {
                    "pos_arg": "192.168.1.2",
                    "opt_args": {
                        "port": 121,
                        "framer": FramerType.ASCII,
                        "source_address": ("195.6.7.8", 1025),
                    },
                    "defaults": {
                        "port": 502,
                        "framer": FramerType.SOCKET,
                        "source_address": None,
                    },
                },
            },
        ],
    )
    @pytest.mark.parametrize(
        ("type_args", "clientclass"),
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
    async def test_client_instanciate(
        self,
        arg_list,
        type_args,
        clientclass,
        test_default,
    ):
        """Try to instantiate clients."""
        cur_args = arg_list[type_args]
        if test_default:
            client = clientclass(cur_args["pos_arg"])
        else:
            client = clientclass(
                cur_args["pos_arg"],
                **arg_list["fix"]["opt_args"],
                **cur_args["opt_args"],
            )

        # Test information methods
        client.last_frame_end = 2
        client.silent_interval = 2
        client.last_frame_end = None

        # a successful execute
        client.transaction = mock.Mock(**{"execute.return_value": True})

        # a unsuccessful connect
        client.connect = lambda: False
        client.transport = None
        pdu = ModbusPDU()
        with pytest.raises(ConnectionException):
            client.execute(False, pdu)

    async def test_client_modbusbaseclient(self):
        """Test modbus base client class."""
        client = ModbusBaseClient(
            FramerType.ASCII,
            3,
            None,
            CommParams(
                host="localhost",
                port=BASE_PORT + 1,
                comm_type=CommType.TCP,
            ),
        )
        client.register(pdu_bit.ReadCoilsResponse)
        assert str(client)
        client.close()

    async def test_client_connection_made(self):
        """Test protocol made connection."""
        client = lib_client.AsyncModbusTcpClient("127.0.0.1")
        assert not client.connected

        transport = mock.AsyncMock()
        transport.close = lambda : ()
        client.ctx.connection_made(transport)
        # assert await client.connected
        client.close()

    async def test_client_base_async(self):
        """Test modbus base client class."""
        async with ModbusBaseClient(
            FramerType.ASCII,
            3,
            None,
            CommParams(
                host="localhost",
                port=BASE_PORT + 2,
                comm_type=CommType.TCP,
            ),
        ) as client:
            str(client)
            client.ctx = mock.Mock()
            client.ctx.connect = mock.AsyncMock(return_value=True)
            assert await client.connect()
            client.ctx.close = mock.Mock()
            client.close()

    async def test_client_protocol(self):
        """Test protocol made connection."""
        client = lib_client.AsyncModbusTcpClient("127.0.0.1")
        client.ctx.loop = mock.Mock()
        client.ctx.callback_connected()
        client.ctx.callback_disconnected(None)
        client = lib_client.AsyncModbusTcpClient("127.0.0.1", on_connect_callback=1)
        client.ctx.loop = mock.Mock()
        client.ctx.callback_connected()
        client.ctx.callback_disconnected(None)
        assert str(client.ctx)

    async def test_client_async_execute(self):
        """Test modbus base client class."""
        async with ModbusBaseClient(
            FramerType.ASCII,
            3,
            None,
            CommParams(
                host="localhost",
                port=BASE_PORT + 2,
                comm_type=CommType.TCP,
            ),
        ) as client:
            str(client)
            client.ctx = mock.Mock()
            client.ctx.execute = mock.AsyncMock(return_value="response")
            assert await client.execute(False, None)

    def test_client_udp_connect(self):
        """Test the Udp client connection method."""
        with mock.patch.object(socket, "socket") as mock_method:

            class DummySocket:
                """Dummy socket."""

                fileno = 1

                def settimeout(self, *a, **kwa):
                    """Set timeout."""

                def setblocking(self, _flag):
                    """Set blocking."""

            mock_method.return_value = DummySocket()
            client = lib_client.ModbusUdpClient("127.0.0.1")
            assert client.connect()

        with mock.patch.object(socket, "socket") as mock_method:
            mock_method.side_effect = OSError()
            client = lib_client.ModbusUdpClient("127.0.0.1")
            assert not client.connect()

    def test_client_tcp_connect(self):
        """Test the tcp client connection method."""
        with mock.patch.object(socket, "create_connection") as mock_method:
            _socket = mock.MagicMock()
            mock_method.return_value = _socket
            client = lib_client.ModbusTcpClient("127.0.0.1")
            _socket.getsockname.return_value = ("dmmy", 1234)
            assert client.connect()

        with mock.patch.object(socket, "create_connection") as mock_method:
            mock_method.side_effect = OSError()
            client = lib_client.ModbusTcpClient("127.0.0.1")
            assert not client.connect()

    def test_client_tcp_reuse(self):
        """Test the tcp client connection method."""
        with mock.patch.object(socket, "create_connection") as mock_method:
            _socket = mock.MagicMock()
            mock_method.return_value = _socket
            client = lib_client.ModbusTcpClient("127.0.0.1")
            _socket.getsockname.return_value = ("dmmy", 1234)
            assert client.connect()
        client.close()
        with mock.patch.object(socket, "create_connection") as mock_method:
            _socket = mock.MagicMock()
            mock_method.return_value = _socket
            client = lib_client.ModbusTcpClient("127.0.0.1")
            _socket.getsockname.return_value = ("dmmy", 1234)
            assert client.connect()
        client.close()

    @pytest.mark.parametrize("use_async", [True, False])
    def test_client_tls_connect(self, use_async):
        """Test the tls client connection method."""
        if use_async:
            sslctx=lib_client.AsyncModbusTlsClient.generate_ssl(
                certfile=get_certificate("crt"),
                keyfile=get_certificate("key"),
            )
        else:
            sslctx=lib_client.ModbusTlsClient.generate_ssl(
                certfile=get_certificate("crt"),
                keyfile=get_certificate("key"),
            )
        with mock.patch.object(ssl.SSLSocket, "connect") as mock_method:
            client = lib_client.ModbusTlsClient(
                "127.0.0.1",
                sslctx=sslctx,
            )
            assert client.connect()

        with mock.patch.object(socket, "create_connection") as mock_method:
            mock_method.side_effect = OSError()
            client = lib_client.ModbusTlsClient("127.0.0.1", sslctx=sslctx)
            assert not client.connect()

    def test_client_tls_connect2(self):
        """Test the tls client connection method."""
        sslctx=lib_client.ModbusTlsClient.generate_ssl(
            certfile=get_certificate("crt"),
            keyfile=get_certificate("key"),
        )
        with mock.patch.object(ssl.SSLSocket, "connect") as mock_method:
            client = lib_client.ModbusTlsClient(
                "127.0.0.1",
                sslctx=sslctx,
                source_address=("0.0.0.0", 0)
            )
            assert client.connect()

        with mock.patch.object(socket, "create_connection") as mock_method:
            mock_method.side_effect = OSError()
            client = lib_client.ModbusTlsClient("127.0.0.1", sslctx=sslctx)
            assert not client.connect()

    def test_tcp_client_register(self):
        """Test tcp client."""

        class CustomRequest:  # pylint: disable=too-few-public-methods
            """Dummy custom request."""

            function_code = 79

        client = lib_client.ModbusTcpClient("127.0.0.1")
        client.framer = mock.Mock()
        client.register(CustomRequest)
        client.framer.decoder.register.assert_called_once_with(CustomRequest)

    def test_idle_time(self):
        """Test idle_time()."""
        client = lib_client.ModbusTcpClient("127.0.0.1")
        assert not client.idle_time()
        client.last_frame_end = None
        assert not client.idle_time()

    def test_start_send(self):
        """Test idle_time()."""
        client = lib_client.ModbusTcpClient("127.0.0.1")
        client.state = ModbusTransactionState.IDLE
        client._start_send()
        client.state = ModbusTransactionState.RETRYING
        client._start_send()

    def test_sync_block(self):
        """Test idle_time()."""
        with lib_client.ModbusTcpClient("127.0.0.1") as client:
            assert not client.connected

    def test_sync_execute(self):
        """Test idle_time()."""
        client = lib_client.ModbusTcpClient("127.0.0.1")
        client.connect = mock.Mock(return_value=False)
        with pytest.raises(ConnectionException):
            client.execute(False, None)
        client.transaction = mock.Mock()
        client.connect.return_value = True
        client.execute(False, None)

    @pytest.mark.parametrize(
        ("client_class"),
        [
            lib_client.AsyncModbusSerialClient,
            lib_client.AsyncModbusTcpClient,
            lib_client.AsyncModbusTlsClient,
            lib_client.AsyncModbusUdpClient,
            lib_client.ModbusSerialClient,
            lib_client.ModbusTcpClient,
            lib_client.ModbusTlsClient,
            lib_client.ModbusUdpClient,
        ])
    async def test_wrong_framer(self, client_class):
        """Check use of wrong framer."""
        with pytest.raises(TypeError):
            client_class("host", framer="dummy")

    async def test_instance_serial(self):
        """Test instantiate."""
        _client = lib_client.AsyncModbusSerialClient("port")

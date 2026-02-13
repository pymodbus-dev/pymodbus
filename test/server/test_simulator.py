"""Test datastore."""

import asyncio
import copy
import json
from unittest import mock

import pytest

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.datastore.simulator import Cell, CellType
from pymodbus.server import ModbusSimulatorServer
from pymodbus.server.simulator.main import run_main
from pymodbus.transport import NULLMODEM_HOST


FX_READ_BIT = 1
FX_READ_REG = 3
FX_WRITE_BIT = 5
FX_WRITE_REG = 6


class TestSimulator:
    """Unittest for the pymodbus.Simutor module."""

    default_device = {
        "setup": {
            "co size": 100,
            "di size": 150,
            "hr size": 200,
            "ir size": 250,
            "shared blocks": True,
            "type exception": False,
            "defaults": {
                "value": {
                    "bits": 0x0708,
                    "uint16": 1,
                    "uint32": 45000,
                    "float32": 127.4,
                    "string": "X",
                },
                "action": {
                    "bits": None,
                    "uint16": None,
                    "uint32": None,
                    "float32": None,
                    "string": None,
                },
            },
        },
        "invalid": [
            1,
            [3, 4],
        ],
        "write": [
            5,
            [7, 8],
            [16, 18],
            [21, 26],
            [33, 38],
        ],
        "bits": [
            5,
            [7, 8],
            {"addr": 10, "value": 0x81},
            {"addr": [11, 12], "value": 0x04342},
            {"addr": 13, "action": "random"},
            {"addr": 14, "value": 15, "action": "reset"},
        ],
        "uint16": [
            {"addr": 16, "value": 3124},
            {"addr": [17, 18], "value": 5678},
            {
                "addr": [19, 20],
                "value": 14661,
                "action": "increment",
                "args": {"minval": 1, "maxval": 100},
            },
        ],
        "uint32": [
            {"addr": [21, 22], "value": 3124},
            {"addr": [23, 26], "value": 5678},
            {"addr": [27, 30], "value": 345000, "action": "increment"},
            {
                "addr": [31, 32],
                "value": 50,
                "action": "random",
                "parameters": {"minval": 10, "maxval": 80},
            },
        ],
        "float32": [
            {"addr": [33, 34], "value": 3124.5},
            {"addr": [35, 38], "value": 5678.19},
            {"addr": [39, 42], "value": 345000.18, "action": "increment"},
        ],
        "string": [
            {"addr": [43, 44], "value": "Str"},
            {"addr": [45, 48], "value": "Strxyz12"},
        ],
        "repeat": [{"addr": [0, 48], "to": [49, 147]}],
    }

    default_server = {
        "server": {
            "comm": "tcp",
            "host": NULLMODEM_HOST,
            "port": 5020,
            "ignore_missing_devices": False,
            "framer": "socket",
            "identity": {
                "VendorName": "pymodbus",
                "ProductCode": "PM",
                "VendorUrl": "https://github.com/pymodbus-dev/pymodbus/",
                "ProductName": "pymodbus Server",
                "ModelName": "pymodbus Server",
                "MajorMinorRevision": "3.1.0",
            },
        },
    }

    test_registers = [
        Cell(),
        Cell(),
        Cell(),
        Cell(),
        Cell(),
        Cell(type=CellType.BITS, access=True, value=0x0708),
        Cell(type=CellType.INVALID),
        Cell(type=CellType.BITS, access=True, value=0x0708),
        Cell(type=CellType.BITS, access=True, value=0x0708),
        Cell(type=CellType.INVALID),
        Cell(type=CellType.BITS, value=0x81),  # 10
        Cell(type=CellType.BITS, value=0x4342),
        Cell(type=CellType.BITS, value=0x4342),
        Cell(type=CellType.BITS, value=1800, action=2),
        Cell(type=CellType.BITS, value=15, action=3),
        Cell(type=CellType.INVALID),
        Cell(type=CellType.UINT16, access=True, value=3124),
        Cell(type=CellType.UINT16, access=True, value=5678),
        Cell(type=CellType.UINT16, access=True, value=5678),
        Cell(type=CellType.UINT16, value=14661, action=1),
        Cell(type=CellType.UINT16, value=14661, action=1),  # 20
        Cell(type=CellType.UINT32, access=True),
        Cell(type=CellType.NEXT, access=True, value=3124),
        Cell(type=CellType.UINT32, access=True),
        Cell(type=CellType.NEXT, access=True, value=5678),
        Cell(type=CellType.UINT32, access=True),
        Cell(type=CellType.NEXT, access=True, value=5678),
        Cell(type=CellType.UINT32, value=5, action=1),
        Cell(type=CellType.NEXT, value=17320),
        Cell(type=CellType.UINT32, value=5, action=1),
        Cell(type=CellType.NEXT, value=17320),  # 30
        Cell(
            type=CellType.UINT32, action=2, action_parameters={"minval": 10, "maxval": 80}
        ),
        Cell(type=CellType.NEXT, value=50),
        Cell(type=CellType.FLOAT32, access=True, value=17731),
        Cell(type=CellType.NEXT, access=True, value=18432),
        Cell(type=CellType.FLOAT32, access=True, value=17841),
        Cell(type=CellType.NEXT, access=True, value=29061),
        Cell(type=CellType.FLOAT32, access=True, value=17841),
        Cell(type=CellType.NEXT, access=True, value=29061),
        Cell(type=CellType.FLOAT32, value=18600, action=1),
        Cell(type=CellType.NEXT, value=29958),  # 40
        Cell(type=CellType.FLOAT32, value=18600, action=1),
        Cell(type=CellType.NEXT, value=29958),
        Cell(type=CellType.STRING, value=int.from_bytes(bytes("St", "utf-8"), "big")),
        Cell(type=CellType.NEXT, value=int.from_bytes(bytes("r ", "utf-8"), "big")),
        Cell(type=CellType.STRING, value=int.from_bytes(bytes("St", "utf-8"), "big")),
        Cell(type=CellType.NEXT, value=int.from_bytes(bytes("rx", "utf-8"), "big")),
        Cell(type=CellType.NEXT, value=int.from_bytes(bytes("yz", "utf-8"), "big")),
        Cell(type=CellType.NEXT, value=int.from_bytes(bytes("12", "utf-8"), "big")),
        # 48 MAX before repeat
    ]

    @staticmethod
    @pytest.fixture(name="use_port")
    def get_port_in_class(base_ports):
        """Return next port."""
        base_ports[__class__.__name__] += 1
        return base_ports[__class__.__name__]

    @classmethod
    def custom_action1(cls, _inx, _cell):
        """Test action."""

    @classmethod
    def custom_action2(cls, _inx, _cell):
        """Test action."""

    custom_actions = {
        "custom1": custom_action1,
        "custom2": custom_action2,
    }

    @pytest.fixture(name="device")
    def copy_default_device(self):
        """Copy default device."""
        return copy.deepcopy(self.default_device)

    @pytest.fixture(name="server")
    def copy_default_server(self, use_port):
        """Create simulator context."""
        server = copy.deepcopy(self.default_server)
        server["server"]["port"] = use_port
        return server

    @pytest.fixture(name="only_object")
    def fixture_only_object(self):
        """Set default only_object."""
        return False

    @pytest.fixture(name="simulator_server")
    async def setup_simulator_server(self, server, device, unused_tcp_port, only_object):
        """Mock open for simulator server."""
        with mock.patch(
            "builtins.open",
            mock.mock_open(
                read_data=json.dumps(
                    {
                        "server_list": server,
                        "device_list": {"device": device},
                    }
                )
            )
        ):
            task = ModbusSimulatorServer(http_port=unused_tcp_port)
            if only_object:
                yield task
            else:
                await task.run_forever(only_start=True)
                await asyncio.sleep(0.5)
                task_future = task.serving
                yield task
                await task.stop()
                await task_future

    async def test_simulator_server_tcp(self, simulator_server):
        """Test init simulator server."""

    async def test_simulator_server(self, server, device, unused_tcp_port):
        """Test init simulator server."""
        server["server"]["device_id"] = 17
        with mock.patch(
            "builtins.open",
            mock.mock_open(
                read_data=json.dumps(
                    {
                        "server_list": server,
                        "device_list": {"device": device},
                    }
                )
            )
        ):
            ModbusSimulatorServer(http_port=unused_tcp_port, custom_actions_module="pymodbus.server.simulator.custom_actions")

    @pytest.mark.parametrize("only_object", [True])
    async def test_simulator_server_exc(self, simulator_server):
        """Test init simulator server."""
        simulator_server.ready_event.set = mock.Mock(side_effect=RuntimeError)
        with pytest.raises(RuntimeError):
            await simulator_server.run_forever()
        await simulator_server.stop()
        await simulator_server.serving

    @pytest.mark.parametrize("only_object", [True])
    async def test_simulator_server_serving(self, simulator_server):
        """Test init simulator server."""
        simulator_server.serving.set_result(True)
        await simulator_server.run_forever()
        await simulator_server.stop()

    async def test_simulator_server_end_to_end(self, simulator_server, use_port):
        """Test simulator server end to end."""
        client = AsyncModbusTcpClient(NULLMODEM_HOST, port=use_port)
        assert await client.connect()
        result = await client.read_holding_registers(16, count=1, device_id=1)
        assert result.registers[0] == 3124
        client.close()

    async def test_simulator_server_string(self, simulator_server, use_port):
        """Test simulator server end to end."""
        client = AsyncModbusTcpClient(NULLMODEM_HOST, port=use_port)
        assert await client.connect()
        result = await client.read_holding_registers(43, count=2, device_id=1)
        assert result.registers[0] == int.from_bytes(bytes("St", "utf-8"), "big")
        assert result.registers[1] == int.from_bytes(bytes("r ", "utf-8"), "big")
        result = await client.read_holding_registers(43, count=6, device_id=1)
        assert result.registers[0] == int.from_bytes(bytes("St", "utf-8"), "big")
        assert result.registers[1] == int.from_bytes(bytes("r ", "utf-8"), "big")
        assert result.registers[2] == int.from_bytes(bytes("St", "utf-8"), "big")
        assert result.registers[3] == int.from_bytes(bytes("rx", "utf-8"), "big")
        assert result.registers[4] == int.from_bytes(bytes("yz", "utf-8"), "big")
        assert result.registers[5] == int.from_bytes(bytes("12", "utf-8"), "big")
        result = await client.read_holding_registers(21, count=23, device_id=1)
        assert len(result.registers) == 23
        client.close()

    async def test_simulator_main(self):
        """Test main."""
        with mock.patch("pymodbus.server.simulator.http_server.ModbusSimulatorServer.run_forever") as server:
            server.return_value = True
            await run_main(cmdline={})
    async def test_simulator_main_file_not_found(self):
        """Test main with missing configuration file."""
        with mock.patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False
            # Usamos side_effect para que sys.exit REALMENTE lance una excepción
            with mock.patch("sys.exit", side_effect=SystemExit(1)) as mock_exit:
                with pytest.raises(SystemExit):
                    await run_main(cmdline=["--json_file", "non_existent.json"])
                mock_exit.assert_called_once_with(1)


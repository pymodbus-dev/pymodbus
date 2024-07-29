"""Test simulator API."""
import asyncio
import json

import pytest
from aiohttp import ClientSession

from pymodbus.server import ModbusSimulatorServer
from pymodbus.server.simulator import http_server


class TestSimulatorApi:
    """Integration tests for the pymodbus.SimutorServer module."""

    default_config = {
        "server_list": {
            "test-device-server": {
                # The test does not care about the server configuration, but
                # they must be present for the simulator to start.
                "comm": "tcp",
                "host": "0.0.0.0",
                "port": 25020,
                "framer": "socket",
            }
        },
        "device_list": {
            "test-device": {
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
        }
    }

    # Fixture to set up the aiohttp app
    @pytest.fixture
    async def client(self, aiohttp_client, tmp_path):
        """Fixture to provide usable aiohttp client for testing."""
        async with ClientSession() as session:
            yield session

    @pytest.fixture
    async def simulator(self, tmp_path):
        """Fixture to provide a standard simulator for testing."""
        config_path = tmp_path / "config.json"
        # Dump the config to a json file for the simulator
        with open(config_path, "w") as file:
            json.dump(self.default_config, file)

        simulator = ModbusSimulatorServer(
            modbus_server = "test-device-server",
            modbus_device = "test-device",
            http_host = "localhost",
            http_port = 18080,
            log_file = "simulator.log",
            json_file = config_path
        )

        # Run the simulator in the current event loop. Store the task so they live
        # until the test is done.
        loop = asyncio.get_running_loop()
        task = loop.create_task(simulator.run_forever(only_start=True))

        # TODO: Make a better way to wait for the simulator to start
        await asyncio.sleep(1)

        yield simulator

        # Stop the simulator after the test is done
        task.cancel()
        await task
        await simulator.stop()

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

    @pytest.mark.asyncio
    async def test_registers_json_valid(self, client, simulator):
        """Test the /restapi/registers endpoint with valid parameters."""
        url = f"http://{simulator.http_host}:{simulator.http_port}/restapi/registers"
        data = {
            "submit": "Registers",
            "range_start": 16,
            "range_stop": 16,
        }

        async with client.post(url, json=data) as resp:
            assert resp.status == 200

            json_response = await resp.json()

            assert "result" in json_response
            assert "footer" in json_response
            assert "register_types" in json_response
            assert "register_actions" in json_response
            assert "register_rows" in json_response

            assert json_response["result"] == "ok"

            # Check that we got the correct register and correct fields. Ignore
            # the contents of the ones that haven't been explicitly set in
            # config, just make sure they are present.
            assert json_response["register_rows"][0]["index"] == "16"
            assert json_response["register_rows"][0]["type"] == "uint16"
            assert json_response["register_rows"][0]["value"] == "3124"
            assert "action" in json_response["register_rows"][0]
            assert "access" in json_response["register_rows"][0]
            assert "count_read" in json_response["register_rows"][0]
            assert "count_write" in json_response["register_rows"][0]

    @pytest.mark.asyncio
    async def test_registers_json_invalid_params(self, client, simulator):
        """Test the /restapi/registers endpoint with invalid parameters."""
        url = f"http://{simulator.http_host}:{simulator.http_port}/restapi/registers"
        data = {
            "submit": "Registers",
            "range_start": "invalid",
            "range_stop": 5,
        }

        async with client.post(url, json=data) as resp:
            # At the moment, errors are stored in the data. Only malformed
            # requests or bad endpoints will return a non-200 status code.
            assert resp.status == 200

            json_response = await resp.json()

            assert "error" in json_response
            assert json_response["error"] == "Invalid range parameters"

    @pytest.mark.asyncio
    async def test_registers_json_non_existent_range(self, client, simulator):
        """Test the /restapi/registers endpoint with a non-existent range."""
        url = f"http://{simulator.http_host}:{simulator.http_port}/restapi/registers"
        data = {
            "submit": "Registers",
            "range_start": 5,
            "range_stop": 7,
        }

        async with client.post(url, json=data) as resp:
            assert resp.status == 200

            json_response = await resp.json()
            assert json_response["result"] == "ok"

            # The simulator should respond with all of the ranges, but the ones that
            # do not exist are marked as "invalid"
            assert len(json_response["register_rows"]) == 3

            assert json_response["register_rows"][0]["index"] == "5"
            assert json_response["register_rows"][0]["type"] == "bits"
            assert json_response["register_rows"][1]["index"] == "6"
            assert json_response["register_rows"][1]["type"] == "invalid"
            assert json_response["register_rows"][2]["index"] == "7"
            assert json_response["register_rows"][2]["type"] == "bits"

    @pytest.mark.asyncio
    async def test_registers_json_set_value(self, client, simulator):
        """Test the /restapi/registers endpoint with a set value request."""
        url = f"http://{simulator.http_host}:{simulator.http_port}/restapi/registers"
        data = {
            "submit": "Set",
            "register": 16,
            "value": 1234,
            # The range parameters are her edue to the API not being properly
            # formed (yet). They are equivalent of form fields that should not
            # be present in a smark json request.
            "range_start": 16,
            "range_stop": 16,
        }

        async with client.post(url, json=data) as resp:
            assert resp.status == 200

            json_response = await resp.json()

            assert "result" in json_response
            assert json_response["result"] == "ok"

            # Check that the value was set correctly
            assert json_response["register_rows"][0]["index"] == "16"
            assert json_response["register_rows"][0]["value"] == "1234"

        # Double check that the value was set correctly, not just the response
        data2 = {
            "submit": "Registers",
            "range_start": 16,
            "range_stop": 16,
        }
        async with client.post(url, json=data2) as resp:
            assert resp.status == 200

            json_response = await resp.json()
            assert json_response["result"] == "ok"

            assert json_response["register_rows"][0]["index"] == "16"
            assert json_response["register_rows"][0]["value"] == "1234"

    @pytest.mark.asyncio
    async def test_registers_json_set_invalid_value(self, client, simulator):
        """Test the /restapi/registers endpoint with an invalid set value request."""
        url = f"http://{simulator.http_host}:{simulator.http_port}/restapi/registers"
        data = {
            "submit": "Set",
            "register": 16,
            "value": "invalid",
        }

        async with client.post(url, json=data) as resp:
            assert resp.status == 200

            json_response = await resp.json()

            assert "error" in json_response
            # Do not check for error content. It is currently
            # unhandled, so it is not guaranteed to be consistent.

    @pytest.mark.parametrize("response_type", [
        http_server.RESPONSE_NORMAL,
        http_server.RESPONSE_ERROR,
        http_server.RESPONSE_EMPTY,
        http_server.RESPONSE_JUNK
    ])
    @pytest.mark.parametrize("call", [
        ("split_delay", 1),
        ("response_cr_pct", 1),
        ("response_delay", 1),
        ("response_error", 1),
        ("response_junk_datalen", 1),
        ("response_clear_after", 1),
    ])
    @pytest.mark.asyncio
    async def test_calls_json_simulate(self, client, simulator, response_type, call):
        """
        Test the /restapi/calls endpoint to make sure simulations are set without errors.

        Some have extra parameters, others don't
        """
        url = f"http://{simulator.http_host}:{simulator.http_port}/restapi/calls"

        # The default arguments which must be present in the request
        data = {
            "submit": "Simulate",
            "response_type": response_type,
            "response_split": "nomatter",
            "split_delay": 0,
            "response_cr": "nomatter",
            "response_cr_pct": 0,
            "response_delay": 0,
            "response_error": 0,
            "response_junk_datalen": 0,
            "response_clear_after": 0,
        }

        # Change the value of one call based on the parameter
        data[call[0]] = call[1]

        async with client.post(url, json=data) as resp:
            assert resp.status == 200

            json_response = await resp.json()
            assert json_response["result"] == "ok"


    @pytest.mark.asyncio
    async def test_calls_json_simulate_reset_no_simulation(self, client, simulator):
        """
        Test the /restapi/calls endpoint with a reset request.

        Just make sure that there will be no error when resetting without triggering
        a simulation.
        """
        url = f"http://{simulator.http_host}:{simulator.http_port}/restapi/calls"

        data = {
            "submit": "Reset",
        }

        async with client.post(url, json=data) as resp:
            assert resp.status == 200

            json_response = await resp.json()
            assert json_response["result"] == "ok"

    @pytest.mark.asyncio
    async def test_calls_json_simulate_reset_with_simulation(self, client, simulator):
        """Test the /restapi/calls endpoint with a reset request after a simulation."""
        url = f"http://{simulator.http_host}:{simulator.http_port}/restapi/calls"

        data = {
            "submit": "Simulate",
            "response_type": http_server.RESPONSE_EMPTY,
            "response_split": "nomatter",
            "split_delay": 0,
            "response_cr": "nomatter",
            "response_cr_pct": 0,
            "response_delay": 100,
            "response_error": 0,
            "response_junk_datalen": 0,
            "response_clear_after": 0,
        }

        async with client.post(url, json=data) as resp:
            assert resp.status == 200

            json_response = await resp.json()
            assert json_response["result"] == "ok"

        data = {
            "submit": "Reset",
        }

        async with client.post(url, json=data) as resp:
            assert resp.status == 200

            json_response = await resp.json()
            assert json_response["result"] == "ok"

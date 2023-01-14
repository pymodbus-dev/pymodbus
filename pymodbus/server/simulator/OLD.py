"""Reactive main."""
from __future__ import annotations

import asyncio
import logging

# pylint: disable=missing-type-doc
import os
import random
import sys
import threading
import time
from enum import Enum


try:
    from aiohttp import web
except ImportError:
    print(
        "Reactive server requires aiohttp. "
        'Please install with "pip install aiohttp" and try again.'
    )
    sys.exit(1)

from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext
from pymodbus.datastore.store import (
    BaseModbusDataBlock,
    ModbusSequentialDataBlock,
    ModbusSparseDataBlock,
)
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.pdu import ExceptionResponse, ModbusExceptions
from pymodbus.server.async_io import (
    ModbusConnectedRequestHandler,
    ModbusDisconnectedRequestHandler,
    ModbusSerialServer,
    ModbusSingleRequestHandler,
    ModbusTcpServer,
    ModbusTlsServer,
    ModbusUdpServer,
)
from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusBinaryFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
    ModbusTlsFramer,
)
from pymodbus.version import version as pymodbus_version


logger = logging.getLogger(__name__)

SERVER_MAPPER = {
    "tcp": ModbusTcpServer,
    "serial": ModbusSerialServer,
    "udp": ModbusUdpServer,
    "tls": ModbusTlsServer,
}

DEFAULT_FRAMER = {
    "tcp": ModbusSocketFramer,
    "rtu": ModbusRtuFramer,
    "tls": ModbusTlsFramer,
    "udp": ModbusSocketFramer,
    "ascii": ModbusAsciiFramer,
    "binary": ModbusBinaryFramer,
}

DEFAULT_MANIPULATOR = {
    "response_type": "normal",  # normal, error, delayed, empty
    "delay_by": 0,
    "error_code": ModbusExceptions.IllegalAddress,
    "clear_after": 5,  # request count
}
DEFUALT_HANDLERS = {
    "ModbusSingleRequestHandler": ModbusSingleRequestHandler,
    "ModbusConnectedRequestHandler": ModbusConnectedRequestHandler,
    "ModbusDisconnectedRequestHandler": ModbusDisconnectedRequestHandler,
}
DEFAULT_MODBUS_MAP = {
    "block_start": 0,
    "block_size": 100,
    "default": 0,
    "sparse": False,
}
DEFAULT_DATA_BLOCK = {
    "co": DEFAULT_MODBUS_MAP,
    "di": DEFAULT_MODBUS_MAP,
    "ir": DEFAULT_MODBUS_MAP,
    "hr": DEFAULT_MODBUS_MAP,
}

HINT = """
Reactive Modbus Server started.
{}

===========================================================================
Example Usage:
curl -X POST http://{}:{} -d "{{"response_type": "error", "error_code": 4}}"
===========================================================================
"""


class ReactiveModbusSlaveContext(ModbusSlaveContext):
    """Reactive Modbus slave context"""

    def __init__(
        self,
        discrete_inputs: BaseModbusDataBlock = None,
        coils: BaseModbusDataBlock = None,
        input_registers: BaseModbusDataBlock = None,
        holding_registers: BaseModbusDataBlock = None,
        zero_mode: bool = False,
        randomize: int = 0,
        change_rate: int = 0,
        **kwargs,
    ):
        """Reactive Modbus slave context supporting simulating data.

        :param discrete_inputs: Discrete input data block
        :param coils: Coils data block
        :param input_registers: Input registers data block
        :param holding_registers: Holding registers data block
        :param zero_mode: Enable zero mode for data blocks
        :param randomize: Randomize reads every <n> reads for DI and IR,
                          default is disabled (0)
        :param change_rate: Rate in % of registers to change for DI and IR,
                          default is disabled (0)
        :param min_binary_value: Minimum value for coils and discrete inputs
        :param max_binary_value: Max value for discrete inputs
        :param min_register_value: Minimum value for input registers
        :param max_register_value: Max value for input registers

        """
        super().__init__(
            di=discrete_inputs,
            co=coils,
            ir=input_registers,
            hr=holding_registers,
            zero_mode=zero_mode,
        )
        min_binary_value = kwargs.get("min_binary_value", 0)
        max_binary_value = kwargs.get("max_binary_value", 1)
        min_register_value = kwargs.get("min_register_value", 0)
        max_register_value = kwargs.get("max_register_value", 65535)
        self._randomize = randomize
        self._change_rate = change_rate
        if self._randomize > 0 and self._change_rate > 0:
            sys.exit(
                "'randomize' and 'change_rate' is not allowed to use at the same time"
            )
        self._lock = threading.Lock()
        self._read_counter = {"d": 0, "i": 0}
        self._min_binary_value = min_binary_value
        self._max_binary_value = max_binary_value
        self._min_register_value = min_register_value
        self._max_register_value = max_register_value

    def getValues(self, fc_as_hex, address, count=1):
        """Get `count` values from datastore.

        :param fc_as_hex: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        if not self.zero_mode:
            address = address + 1
        txt = f"getValues: fc-[{fc_as_hex}] address-{address}: count-{count}"
        logger.debug(txt)
        _block_type = self.decode(fc_as_hex)
        if self._randomize > 0 and _block_type in {"d", "i"}:
            with self._lock:
                if not (self._read_counter.get(_block_type) % self._randomize):
                    # Update values
                    if _block_type == "d":
                        min_val = self._min_binary_value
                        max_val = self._max_binary_value
                    else:
                        min_val = self._min_register_value
                        max_val = self._max_register_value
                    values = [random.randint(min_val, max_val) for _ in range(count)]
                    # logger.debug("Updating '%s' with values '%s' starting at "
                    #              "'%s'", _block_type, values, address)
                    self.store[_block_type].setValues(address, values)
                self._read_counter[_block_type] += 1
        elif self._change_rate > 0 and _block_type in {"d", "i"}:
            regs_to_changes = round(count * self._change_rate / 100)
            random_indices = random.sample(range(count), regs_to_changes)
            for offset in random_indices:
                with self._lock:
                    # Update values
                    if _block_type == "d":
                        min_val = self._min_binary_value
                        max_val = self._max_binary_value
                    else:
                        min_val = self._min_register_value
                        max_val = self._max_register_value
                    self.store[_block_type].setValues(
                        address + offset, random.randint(min_val, max_val)
                    )
        values = self.store[_block_type].getValues(address, count)
        return values


class ReactiveServer:
    """Modbus Asynchronous Server which can manipulate the response dynamically.

    Useful for testing
    """

    def __init__(self, host, port, modbus_server):
        """Initialize."""
        self._web_app = web.Application()
        self._runner = web.AppRunner(self._web_app)
        self._host = host
        self._port = int(port)
        self._modbus_server = modbus_server
        self._add_routes()
        self._counter = 0
        self._modbus_server.response_manipulator = self.manipulate_response
        self._manipulator_config = dict(**DEFAULT_MANIPULATOR)
        self._web_app.on_startup.append(self.start_modbus_server)
        self._web_app.on_shutdown.append(self.stop_modbus_server)

    @property
    def web_app(self):
        """Start web_app."""
        return self._web_app

    @property
    def manipulator_config(self):
        """Manipulate config."""
        return self._manipulator_config

    @manipulator_config.setter
    def manipulator_config(self, value):
        if isinstance(value, dict):
            self._manipulator_config.update(**value)

    def _add_routes(self):
        """Add routes."""
        self._web_app.add_routes([web.post("/", self._response_manipulator)])

    async def start_modbus_server(self, app):
        """Start Modbus server as asyncio task after startup.

        :param app: Webapp
        """
        try:
            if hasattr(asyncio, "create_task"):
                if isinstance(self._modbus_server, ModbusSerialServer):
                    app["modbus_serial_server"] = asyncio.create_task(
                        self._modbus_server.start()
                    )
                app["modbus_server"] = asyncio.create_task(
                    self._modbus_server.serve_forever()
                )
            else:
                if isinstance(self._modbus_server, ModbusSerialServer):
                    app["modbus_serial_server"] = asyncio.ensure_future(
                        self._modbus_server.start()
                    )
                app["modbus_server"] = asyncio.ensure_future(
                    self._modbus_server.serve_forever()
                )

            logger.info("Modbus server started")

        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error starting modbus server")
            logger.error(exc)

    async def stop_modbus_server(self, app):
        """Stop modbus server.

        :param app: Webapp
        """
        logger.info("Stopping modbus server")
        if isinstance(self._modbus_server, ModbusSerialServer):
            app["modbus_serial_server"].cancel()
        app["modbus_server"].cancel()
        await app["modbus_server"]
        logger.info("Modbus server Stopped")

    async def _response_manipulator(self, request):
        """POST request Handler for response manipulation end point.

        Payload is a dict with following fields
            :response_type : One among (normal, delayed, error, empty, stray)
            :error_code: Modbus error code for error response
            :delay_by: Delay sending response by <n> seconds

        :param request:
        :return:
        """
        data = await request.json()
        self._manipulator_config.update(data)
        return web.json_response(data=data)

    def update_manipulator_config(self, config):
        """Update manipulator config. Resets previous counters.

        :param config: Manipulator config (dict)
        """
        self._counter = 0
        self._manipulator_config = config

    def manipulate_response(self, response):
        """Manipulate the actual response according to the required error state.

        :param response: Modbus response object
        :return: Modbus response
        """
        skip_encoding = False
        if not self._manipulator_config:
            return response

        clear_after = self._manipulator_config.get("clear_after")
        if clear_after and self._counter > clear_after:
            txt = f"Resetting manipulator after {clear_after} responses"
            logger.info(txt)
            self.update_manipulator_config(dict(DEFAULT_MANIPULATOR))
            return response
        response_type = self._manipulator_config.get("response_type")
        if response_type == "error":
            error_code = self._manipulator_config.get("error_code")
            logger.warning("Sending error response for all incoming requests")
            err_response = ExceptionResponse(response.function_code, error_code)
            err_response.transaction_id = response.transaction_id
            err_response.unit_id = response.unit_id
            response = err_response
            self._counter += 1
        elif response_type == "delayed":
            delay_by = self._manipulator_config.get("delay_by")
            txt = f"Delaying response by {delay_by}s for all incoming requests"
            logger.warning(txt)
            time.sleep(delay_by)  # change to async
            self._counter += 1
        elif response_type == "empty":
            logger.warning("Sending empty response")
            self._counter += 1
            response.should_respond = False
        elif response_type == "stray":
            if (data_len := self._manipulator_config.get("data_len", 10)) <= 0:
                txt = f"Invalid data_len {data_len}, using default 10"
                logger.warning(txt)
                data_len = 10
            response = os.urandom(data_len)
            self._counter += 1
            skip_encoding = True
        return response, skip_encoding

    async def run_async(self, repl_mode=False):
        """Run Web app."""

        try:
            await self._runner.setup()
            site = web.TCPSite(self._runner, self._host, self._port)
            await site.start()
            if not repl_mode:
                message = (
                    f"======== Running on http://{self._host}:{self._port} ========"
                )
                msg = HINT.format(message, self._host, self._port)
                print(msg)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error(exc)

    @classmethod
    def create_identity(
        cls,
        vendor="Pymodbus",
        product_code="PM",
        vendor_url="https://github.com/riptideio/pymodbus/",
        product_name="Pymodbus Server",
        model_name="Reactive Server",
        version=pymodbus_version.short(),
    ):
        """Create modbus identity.

        :param vendor:
        :param product_code:
        :param vendor_url:
        :param product_name:
        :param model_name:
        :param version:
        :return: ModbusIdentity object
        """
        identity = ModbusDeviceIdentification(
            info_name={
                "VendorName": vendor,
                "ProductCode": product_code,
                "VendorUrl": vendor_url,
                "ProductName": product_name,
                "ModelName": model_name,
                "MajorMinorRevision": version,
            }
        )

        return identity

    @classmethod
    def create_context(
        cls,
        data_block_settings: dict = {},
        unit: list[int] = [1],
        single: bool = False,
        randomize: int = 0,
        change_rate: int = 0,
    ):  # pylint: disable=dangerous-default-value
        """Create Modbus context.

        :param data_block_settings: Datablock (dict) Refer DEFAULT_DATA_BLOCK
        :param unit: Unit id for the slave
        :param single: To run as a single slave
        :param randomize: Randomize every <n> reads for DI and IR.
        :param change_rate: Rate in % of registers to change for DI and IR.
        :return: ModbusServerContext object
        """
        data_block = data_block_settings.pop("data_block", DEFAULT_DATA_BLOCK)
        if not isinstance(unit, list):
            unit = [unit]
        slaves = {}
        for i in unit:
            block = {}
            for modbus_entity, block_desc in data_block.items():
                start_address = block_desc.get("block_start", 0)
                default_count = block_desc.get("block_size", 0)
                default_value = block_desc.get("default", 0)
                default_values = [default_value] * default_count
                sparse = block_desc.get("sparse", False)
                db = ModbusSequentialDataBlock if not sparse else ModbusSparseDataBlock
                if sparse:
                    if not (address_map := block_desc.get("address_map")):
                        address_map = random.sample(
                            range(start_address + 1, default_count), default_count - 1
                        )
                        address_map.insert(0, 0)
                    block[modbus_entity] = {
                        add: val
                        for add in sorted(address_map)
                        for val in default_values
                    }
                else:
                    block[modbus_entity] = db(start_address, default_values)

            slave_context = ReactiveModbusSlaveContext(
                **block,
                randomize=randomize,
                change_rate=change_rate,
                zero_mode=True,
                **data_block_settings,
            )
            if not single:
                slaves[i] = slave_context
            else:
                slaves = slave_context
        server_context = ModbusServerContext(slaves, single=single)
        return server_context

    @classmethod
    def factory(  # pylint: disable=dangerous-default-value,too-many-arguments
        cls,
        server,
        framer=None,
        context=None,
        unit=1,
        single=False,
        host="localhost",
        modbus_port=5020,
        web_port=8080,
        data_block_settings={"data_block": DEFAULT_DATA_BLOCK},
        identity=None,
        **kwargs,
    ):
        """Create ReactiveModbusServer.

        :param server: Modbus server type (tcp, rtu, tls, udp)
        :param framer: Modbus framer (ModbusSocketFramer, ModbusRTUFramer, ModbusTLSFramer)
        :param context: Modbus server context to use
        :param unit: Modbus unit id
        :param single: Run in single mode
        :param host: Host address to use for both web app and modbus server (default localhost)
        :param modbus_port: Modbus port for TCP and UDP server(default: 5020)
        :param web_port: Web App port (default: 8080)
        :param data_block_settings: Datablock settings (refer DEFAULT_DATA_BLOCK)
        :param identity: Modbus identity object
        :param kwargs: Other server specific keyword arguments,
        :              refer corresponding servers documentation
        :return: ReactiveServer object
        """
        if isinstance(server, Enum):
            server = server.value

        if server.lower() not in SERVER_MAPPER:
            txt = f"Invalid server {server}"
            logger.error(txt)
            sys.exit(1)
        server = SERVER_MAPPER.get(server)
        randomize = kwargs.pop("randomize", 0)
        change_rate = kwargs.pop("change_rate", 0)
        if not framer:
            framer = DEFAULT_FRAMER.get(server)
        if not context:
            context = cls.create_context(
                data_block_settings=data_block_settings,
                unit=unit,
                single=single,
                randomize=randomize,
                change_rate=change_rate,
            )
        if not identity:
            identity = cls.create_identity()
        if server == ModbusSerialServer:
            kwargs["port"] = modbus_port
            server = server(context, framer=framer, identity=identity, **kwargs)
        else:
            server = server(
                context,
                framer=framer,
                identity=identity,
                address=(host, modbus_port),
                defer_start=False,
                **kwargs,
            )
        return ReactiveServer(host, web_port, server)

"""
Copyright (c) 2020 by RiptideIO
All rights reserved.
"""
import os
import asyncio
import time
import random
import logging
from pymodbus.version import version as pymodbus_version
from pymodbus.compat import IS_PYTHON3, PYTHON_VERSION
from pymodbus.pdu import ExceptionResponse, ModbusExceptions
from pymodbus.datastore.store import (ModbusSparseDataBlock,
                                      ModbusSequentialDataBlock)
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.device import ModbusDeviceIdentification

if not IS_PYTHON3 or PYTHON_VERSION < (3, 6):
    print(f"You are running {PYTHON_VERSION}."
          "Reactive server requires python3.6 or above")
    exit()


try:
    from aiohttp import web
except ImportError as e:
    print("Reactive server requires aiohttp. "
          "Please install with 'pip install aiohttp' and try again.")
    exit(1)

from pymodbus.server.async_io import (ModbusTcpServer,
                                      ModbusTlsServer,
                                      ModbusSerialServer,
                                      ModbusUdpServer,
                                      ModbusSingleRequestHandler,
                                      ModbusConnectedRequestHandler,
                                      ModbusDisconnectedRequestHandler)
from pymodbus.transaction import (ModbusRtuFramer,
                                  ModbusSocketFramer,
                                  ModbusTlsFramer,
                                  ModbusAsciiFramer,
                                  ModbusBinaryFramer)
logger = logging.getLogger(__name__)

SERVER_MAPPER = {
    "tcp": ModbusTcpServer,
    "serial": ModbusSerialServer,
    "udp": ModbusUdpServer,
    "tls": ModbusTlsServer
}

DEFAULT_FRAMER = {
    "tcp": ModbusSocketFramer,
    "rtu": ModbusRtuFramer,
    "tls": ModbusTlsFramer,
    "udp": ModbusSocketFramer,
    "ascii": ModbusAsciiFramer,
    "binary": ModbusBinaryFramer
}

DEFAULT_MANIPULATOR = {
    "response_type": "normal",  # normal, error, delayed, empty
    "delay_by": 0,
    "error_code": ModbusExceptions.IllegalAddress,
    "clear_after": 5  # request count

}
DEFUALT_HANDLERS = {
    "ModbusSingleRequestHandler": ModbusSingleRequestHandler,
    "ModbusConnectedRequestHandler": ModbusConnectedRequestHandler,
    "ModbusDisconnectedRequestHandler": ModbusDisconnectedRequestHandler
}
DEFAULT_MODBUS_MAP = {"start_offset": 0,
                      "count": 100,
                      "value": 0, "sparse": False}
DEFAULT_DATA_BLOCK = {
    "co": DEFAULT_MODBUS_MAP,
    "di": DEFAULT_MODBUS_MAP,
    "ir": DEFAULT_MODBUS_MAP,
    "hr": DEFAULT_MODBUS_MAP

}

HINT = """
Reactive Modbus Server started.
{}

===========================================================================
Example Usage:
curl -X POST http://{}:{} -d '{{"response_type": "error", "error_code": 4}}'
===========================================================================
"""


class ReactiveServer:
    """
    Modbus Asynchronous Server which can manipulate the response dynamically.
    Useful for testing
    """
    def __init__(self, host, port, modbus_server, loop=None):
        self._web_app = web.Application()
        self._runner = web.AppRunner(self._web_app)
        self._host = host
        self._port = int(port)
        self._modbus_server = modbus_server
        self._loop = loop
        self._add_routes()
        self._counter = 0
        self._modbus_server.response_manipulator = self.manipulate_response
        self._manipulator_config = dict(**DEFAULT_MANIPULATOR)
        self._web_app.on_startup.append(self.start_modbus_server)
        self._web_app.on_shutdown.append(self.stop_modbus_server)

    @property
    def web_app(self):
        return self._web_app

    @property
    def manipulator_config(self):
        return self._manipulator_config

    @manipulator_config.setter
    def manipulator_config(self, value):
        if isinstance(value, dict):
            self._manipulator_config.update(**value)

    def _add_routes(self):
        self._web_app.add_routes([
            web.post('/', self._response_manipulator)])

    async def start_modbus_server(self, app):
        """
        Start Modbus server as asyncio task after startup
        :param app: Webapp
        :return:
        """
        try:
            if hasattr(asyncio, "create_task"):
                if isinstance(self._modbus_server, ModbusSerialServer):
                    app["modbus_serial_server"] = asyncio.create_task(
                        self._modbus_server.start())
                app["modbus_server"] = asyncio.create_task(
                    self._modbus_server.serve_forever())
            else:
                if isinstance(self._modbus_server, ModbusSerialServer):
                    app["modbus_serial_server"] = asyncio.ensure_future(
                        self._modbus_server.start()
                    )
                app["modbus_server"] = asyncio.ensure_future(
                    self._modbus_server.serve_forever())

            logger.info("Modbus server started")
        except Exception as e:
            logger.error("Error starting modbus server")
            logger.error(e)

    async def stop_modbus_server(self, app):
        """
        Stop modbus server
        :param app: Webapp
        :return:
        """
        logger.info("Stopping modbus server")
        if isinstance(self._modbus_server, ModbusSerialServer):
            app["modbus_serial_server"].cancel()
        app["modbus_server"].cancel()
        await app["modbus_server"]
        logger.info("Modbus server Stopped")

    async def _response_manipulator(self, request):
        """
        POST request Handler for response manipulation end point
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
        """
        Updates manipulator config. Resets previous counters
        :param config: Manipulator config (dict)
        :return:
        """
        self._counter = 0
        self._manipulator_config = config

    def manipulate_response(self, response):
        """
        Manipulates the actual response according to the required error state.
        :param response: Modbus response object
        :return: Modbus response
        """
        skip_encoding = False
        if not self._manipulator_config:
            return response
        else:
            clear_after = self._manipulator_config.get("clear_after")
            if clear_after and self._counter > clear_after:
                logger.info("Resetting manipulator"
                            " after {} responses".format(clear_after))
                self.update_manipulator_config(dict(DEFAULT_MANIPULATOR))
                return response
            response_type = self._manipulator_config.get("response_type")
            if response_type == "error":
                error_code = self._manipulator_config.get("error_code")
                logger.warning(
                    "Sending error response for all incoming requests")
                err_response = ExceptionResponse(response.function_code, error_code)
                err_response.transaction_id = response.transaction_id
                err_response.unit_id = response.unit_id
                response = err_response
                self._counter += 1
            elif response_type == "delayed":
                delay_by = self._manipulator_config.get("delay_by")
                logger.warning(
                    "Delaying response by {}s for "
                    "all incoming requests".format(delay_by))
                time.sleep(delay_by)
                self._counter += 1
            elif response_type == "empty":
                logger.warning("Sending empty response")
                self._counter += 1
                response.should_respond = False
            elif response_type == "stray":
                data_len = self._manipulator_config.get("data_len", 10)
                if data_len <= 0:
                    logger.warning(f"Invalid data_len {data_len}. "
                                   f"Using default lenght 10")
                    data_len = 10
                response = os.urandom(data_len)
                self._counter += 1
                skip_encoding = True
            return response, skip_encoding

    def run(self):
        """
        Run Web app
        :return:
        """
        def _info(message):
            msg = HINT.format(message, self._host, self._port)
            print(msg)
            # print(message)
        web.run_app(self._web_app, host=self._host, port=self._port,
                    print=_info)

    async def run_async(self):
        """
        Run Web app
        :return:
        """
        try:
            await self._runner.setup()
            site = web.TCPSite(self._runner, self._host, self._port)
            await site.start()
        except Exception as e:
            logger.error(e)

    @classmethod
    def create_identity(cls, vendor="Pymodbus", product_code="PM",
                        vendor_url='http://github.com/riptideio/pymodbus/',
                        product_name="Pymodbus Server",
                        model_name="Reactive Server",
                        version=pymodbus_version.short()):
        """
        Create modbus identity
        :param vendor:
        :param product_code:
        :param vendor_url:
        :param product_name:
        :param model_name:
        :param version:
        :return: ModbusIdentity object
        """
        identity = ModbusDeviceIdentification()
        identity.VendorName = vendor
        identity.ProductCode = product_code
        identity.VendorUrl = vendor_url
        identity.ProductName = product_name
        identity.ModelName = model_name
        identity.MajorMinorRevision = version

        return identity

    @classmethod
    def create_context(cls, data_block=None, unit=1,
                       single=False):
        """
        Create Modbus context.
        :param data_block: Datablock (dict) Refer DEFAULT_DATA_BLOCK
        :param unit: Unit id for the slave
        :param single: To run as a single slave
        :return: ModbusServerContext object
        """
        block = dict()
        data_block = data_block or DEFAULT_DATA_BLOCK
        for modbus_entity, block_desc in data_block.items():
            start_address = block_desc.get("start_address", 0)
            default_count = block_desc.get("count", 0)
            default_value = block_desc.get("value", 0)
            default_values = [default_value]*default_count
            sparse = block_desc.get("sparse", False)
            db = ModbusSequentialDataBlock if not sparse else ModbusSparseDataBlock
            if sparse:
                address_map = block_desc.get("address_map")
                if not address_map:
                    address_map = random.sample(
                        range(start_address+1, default_count), default_count-1)
                    address_map.insert(0, 0)
                block[modbus_entity] = {add: val for add in sorted(address_map) for val in default_values}
            else:
                block[modbus_entity] =db(start_address, default_values)

        slave_context = ModbusSlaveContext(**block, zero_mode=True)
        if not single:
            slaves = {}
            for i in unit:
                slaves[i] = slave_context
        else:
            slaves = slave_context
        server_context = ModbusServerContext(slaves, single=single)
        return server_context

    @classmethod
    def factory(cls, server, framer=None, context=None, unit=1, single=False,
                host="localhost", modbus_port=5020, web_port=8080,
                data_block=DEFAULT_DATA_BLOCK, identity=None, loop=None, **kwargs):
        """
        Factory to create ReactiveModbusServer
        :param server: Modbus server type (tcp, rtu, tls, udp)
        :param framer: Modbus framer (ModbusSocketFramer, ModbusRTUFramer, ModbusTLSFramer)
        :param context: Modbus server context to use
        :param unit: Modbus unit id
        :param single: Run in single mode
        :param host: Host address to use for both web app and modbus server (default localhost)
        :param modbus_port: Modbus port for TCP and UDP server(default: 5020)
        :param web_port: Web App port (default: 8080)
        :param data_block: Datablock (refer DEFAULT_DATA_BLOCK)
        :param identity: Modbus identity object
        :param loop: Asyncio loop to use
        :param kwargs: Other server specific keyword arguments, refer corresponding servers documentation
        :return: ReactiveServer object
        """
        if server.lower() not in SERVER_MAPPER:
            logger.error(f"Invalid server {server}", server)
            exit(1)
        server = SERVER_MAPPER.get(server)
        if not framer:
            framer = DEFAULT_FRAMER.get(server)
        if not context:
            context = cls.create_context(data_block=data_block,
                                         unit=unit, single=single)
        if not identity:
            identity = cls.create_identity()
        if server == ModbusSerialServer:
            kwargs["port"] = modbus_port
            server = server(context, framer=framer, identity=identity,
                            **kwargs)
        else:
            server = server(context, framer=framer, identity=identity,
                            address=(host, modbus_port), defer_start=False,
                            **kwargs)
        return ReactiveServer(host, web_port, server, loop)

# __END__

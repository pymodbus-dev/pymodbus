"""HTTP server for modbus simulator."""
import asyncio
import importlib
import json
import logging
import os


try:
    from aiohttp import web
except ImportError:
    web = None

from pymodbus.datastore import ModbusServerContext, ModbusSimulatorContext
from pymodbus.datastore.simulator import (
    CELL_TYPE_BIT,
    CELL_TYPE_FLOAT32,
    CELL_TYPE_INVALID,
    CELL_TYPE_NEXT,
    CELL_TYPE_NONE,
    CELL_TYPE_STRING,
    CELL_TYPE_UINT16,
    CELL_TYPE_UINT32,
    Label,
)
from pymodbus.server import (
    ModbusSerialServer,
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


_logger = logging.getLogger(__name__)

MAX_FILTER = 200


class ModbusSimulatorServer:
    """**ModbusSimulatorServer**.

    :param modbus_server: Server name in json file (default: "server")
    :param modbus_device: Device name in json file (default: "client")
    :param http_host: TCP host for HTTP (default: 8080)
    :param http_port: TCP port for HTTP (default: "localhost")
    :param json_file: setup file (default: "setup.json")
    :param custom_actions_module: python module with custom actions (default: none)

    if either http_port or http_host is none, HTTP will not be started.
    This class starts a http server, that serves a couple of endpoints:

    - **"<addr>/"** standard entry index.html (see html.py)
    - **"<addr>/web"** standard entry for web pages (see html.py)
    - **"<addr>/log"** standard entry for server log (see html.py)
    - **"<addr>/api"** REST-API general calls(see rest_api.py)
    - **"<addr>/api/register"** REST-API for register handling (uses datastore/simulator)
    - **"<addr>/api/function"** REST-API for function handling (uses Modbus<x>RequestHandler)

    Example::

        from pymodbus.server import StartAsyncSimulatorServer

        async def run():
            simulator = StartAsyncSimulatorServer(
                modbus_server="my server",
                modbus_device="my device",
                http_host="localhost",
                http_port=8080)
            await simulator.start()
            ...
            await simulator.close()
    """

    def __init__(
        self,
        modbus_server: str = "server",
        modbus_device: str = "device",
        http_host: str = "0.0.0.0",
        http_port: int = 8080,
        log_file: str = "server.log",
        json_file: str = "setup.json",
        custom_actions_module: str = None,
    ):
        """Initialize http interface."""
        if not web:
            raise RuntimeError("aiohttp not installed!")
        with open(json_file, encoding="utf-8") as file:
            setup = json.load(file)

        comm_class = {
            "serial": ModbusSerialServer,
            "tcp": ModbusTcpServer,
            "tls": ModbusTlsServer,
            "udp": ModbusUdpServer,
        }
        framer_class = {
            "ascii": ModbusAsciiFramer,
            "binary": ModbusBinaryFramer,
            "rtu": ModbusRtuFramer,
            "socket": ModbusSocketFramer,
            "tls": ModbusTlsFramer,
        }
        if custom_actions_module:
            actions_module = importlib.import_module(custom_actions_module)
            custom_actions_module = actions_module.custom_actions_dict
        server = setup["server_list"][modbus_server]
        device = setup["device_list"][modbus_device]
        self.datastore_context = ModbusSimulatorContext(device, custom_actions_module)
        datastore = ModbusServerContext(slaves=self.datastore_context, single=True)
        comm = comm_class[server.pop("comm")]
        framer = framer_class[server.pop("framer")]
        self.modbus_server = comm(framer=framer, context=datastore, **server)

        self.log_file = log_file
        self.site = None
        self.http_host = http_host
        self.http_port = http_port
        self.web_path = os.path.join(os.path.dirname(__file__), "web")
        self.web_app = web.Application()
        self.web_app.add_routes(
            [
                web.get("/api/{tail:[a-z]*}", self.handle_html),
                web.post("/api/{tail:[a-z]*}", self.handle_json),
                web.get("/{tail:[a-z0-9.]*}", self.handle_html_static),
                web.get("/", self.handle_html_static),
            ]
        )
        self.web_app.on_startup.append(self.start_modbus_server)
        self.web_app.on_shutdown.append(self.stop_modbus_server)
        self.generator_html = {
            "log": [None, self.build_html_log],
            "registers": [None, self.build_html_registers],
            "calls": [None, self.build_html_calls],
            "server": [None, self.build_html_server],
        }
        for entry in self.generator_html:  # pylint: disable=consider-using-dict-items
            file = os.path.join(self.web_path, "generator", entry)
            with open(file, encoding="utf-8") as handle:
                self.generator_html[entry][0] = handle.read()
        self.refresh_rate = 0
        self.register_filter = []

    async def start_modbus_server(self, app):
        """Start Modbus server as asyncio task."""
        try:
            if getattr(self.modbus_server, "start", None):
                await self.modbus_server.start()
            app["modbus_server"] = asyncio.create_task(
                self.modbus_server.serve_forever()
            )
        except Exception as exc:
            txt = f"Error starting modbus server, reason: {exc}"
            _logger.error(txt)
            raise exc
        _logger.info("Modbus server started")

    async def stop_modbus_server(self, app):
        """Stop modbus server."""
        _logger.info("Stopping modbus server")
        app["modbus_server"].cancel()
        await app["modbus_server"]
        _logger.info("Modbus server Stopped")

    def run_forever(self):
        """Start modbus and http servers."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            runner = web.AppRunner(self.web_app)
            loop.run_until_complete(runner.setup())
            self.site = web.TCPSite(runner, self.http_host, self.http_port)
            loop.run_until_complete(self.site.start())
        except Exception as exc:
            txt = f"Error starting http server, reason: {exc}"
            _logger.error(txt)
            raise exc
        _logger.info("HTTP server started")
        loop.run_forever()

    async def stop(self):
        """Stop modbus and http servers."""
        self.site.stop()
        self.site = None

    async def handle_html_static(self, request):
        """Handle static html."""
        if (page := request.path[1:]) == "":  # pylint: disable=compare-to-empty-string
            page = "index.html"
        file = os.path.join(self.web_path, page)
        try:
            with open(file, encoding="utf-8"):
                return web.FileResponse(file)
        except (FileNotFoundError, IsADirectoryError) as exc:
            raise web.HTTPNotFound(reason="File not found") from exc

    async def handle_html(self, request):
        """Handle html."""
        page_type = request.path.split("/")[-1]
        params = dict(request.query)
        if refresh := params.pop("refresh", None):
            self.refresh_rate = int(refresh)
        if self.refresh_rate > 0:
            html = self.generator_html[page_type][0].replace(
                "<!--REFRESH-->",
                f'<meta http-equiv="refresh" content="{self.refresh_rate}">',
            )
        else:
            html = self.generator_html[page_type][0].replace("<!--REFRESH-->", "")
        new_page = await self.generator_html[page_type][1](params, html)
        return web.Response(text=new_page, content_type="text/html")

    async def handle_json(self, request):
        """Handle api registers."""
        action = request.path.split("/")[-1]
        params = await request.post()
        return web.Response(text=f"json build: {action} - {params}")

    async def build_html_log(self, _params, html):
        """Build html log page."""
        return html

    async def build_html_registers(self, params, html):  # pylint: disable=too-complex
        """Build html log page."""
        register_foot = ""
        register_types = ""
        for name, xtype in self.datastore_context.type_names.items():
            register_types += f"<option value={xtype} selected>{name}</option>"
        register_actions = ""
        for name, action in self.datastore_context.action_names.items():
            if name is None:
                name = "Any"
            if action is None:
                action = 0
            register_actions += f"<option value={action} selected>{name}</option>"
        html = html.replace("<!--REGISTER_ACTIONS-->", register_actions).replace(
            "<!--REGISTER_TYPES-->", register_types
        )

        if params["submit"] == "Add":
            res_ok, result_txt = self.helper_build_filter(params)
            if not res_ok:
                return html.replace("<!--RESULT-->", result_txt)
        elif params["submit"] == "Clear":  # pylint: disable=confusing-consecutive-elif
            self.register_filter = []
        elif params["submit"] == "Set":
            if not (register := params["register"]):
                return html.replace("<!--RESULT-->", "Missing register")
            register = int(register)
            if not (value := params["value"]):
                self.datastore_context.registers[register].value = int(value)
            if bool(params.get("writeable", False)):
                self.datastore_context.registers[register].access = True
        rows = ""
        for i in self.register_filter:
            reg = self.datastore_context.registers[i]
            inx = f"{i}"
            value = reg.value
            if reg.type == CELL_TYPE_INVALID:
                xtype = Label.invalid
            elif reg.type == CELL_TYPE_NONE:
                xtype = Label.type_none
            elif reg.type == CELL_TYPE_BIT:
                xtype = Label.type_bits
            elif reg.type == CELL_TYPE_NEXT:
                continue
            elif reg.type == CELL_TYPE_UINT16:
                xtype = Label.type_uint16
            elif reg.type == CELL_TYPE_UINT32:
                xtype = Label.type_uint32
                inx = f"{i}-{i+1}"
                tmp_regs = [value, self.datastore_context.registers[i + 1].value]
                value = self.datastore_context.build_value_from_registers(
                    tmp_regs, True
                )
            elif reg.type == CELL_TYPE_FLOAT32:
                xtype = Label.type_float32
                inx = f"{i}-{i+1}"
                tmp_regs = [value, self.datastore_context.registers[i + 1].value]
                value = self.datastore_context.build_value_from_registers(
                    tmp_regs, False
                )
            elif reg.type == CELL_TYPE_STRING:
                xtype = Label.type_string
                inx = f"{i}-{i+1}"
                j = i
                value = ""
                while True:
                    tmp_value = self.datastore_context.registers[j].value
                    value += str(
                        tmp_value.to_bytes(2, "big"), encoding="utf-8", errors="ignore"
                    )
                    j += 1
                    if self.datastore_context.registers[j].type != CELL_TYPE_NEXT:
                        break
                inx = f"{i}-{j-1}"

            else:
                xtype = "????"
            action = self.datastore_context.action_inx_to_name[reg.action]
            rows += f"<tr><td>{inx}</td><td>{xtype}</td><td>{reg.access}</td><td>{action}</td><td>{value}</td><td>{reg.count_read}</td><td>{reg.count_write}</td></tr>"

        new_html = (
            html.replace("<!--REGISTER_FOOT-->", register_foot)
            .replace("<!--REGISTER_ROWS-->", rows)
            .replace("<!--RESULT-->", "ok")
        )
        return new_html

    async def build_html_calls(self, _params, html):
        """Build html log page."""
        return html

    async def build_html_server(self, _params, html):
        """Build html log page."""
        return html

    def helper_build_filter(self, params):  # pylint: disable=too-complex
        """Build list of registers matching filter."""
        if range_start := params["range_start"]:
            range_start = int(range_start)
        else:
            range_start = None
        if range_stop := params["range_stop"]:
            range_stop = int(range_stop)
        else:
            range_stop = range_start
        action = int(params["action"])
        writeable = "writeable" in params
        filter_updated = 0
        if range_start:
            steps = range(range_start, range_stop)
        else:
            steps = range(1, self.datastore_context.register_count)
        for i in steps:
            if range_start and (i < range_start or i > range_stop):
                continue
            reg = self.datastore_context.registers[i]
            if writeable and not reg.access:
                continue
            if type and reg.type != type:
                continue
            if action and reg.action != action:
                continue
            if i not in self.register_filter:
                self.register_filter.append(i)
                filter_updated += 1
                if len(self.register_filter) > MAX_FILTER:
                    return False, f"Max. filter size {MAX_FILTER} exceeded!"
        self.register_filter.sort()
        txt = (
            f"Added {filter_updated} registers."
            if filter_updated
            else "NO registers added."
        )
        return True, txt

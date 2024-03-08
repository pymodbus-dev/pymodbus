"""HTTP server for modbus simulator."""
from __future__ import annotations

import asyncio
import contextlib
import dataclasses
import importlib
import json
import os
from time import sleep
from typing import TYPE_CHECKING


try:
    from aiohttp import web

    AIOHTTP_MISSING = False
except ImportError:
    AIOHTTP_MISSING = True
    if TYPE_CHECKING:  # always False at runtime
        # type checkers do not understand the Raise RuntimeError in __init__()
        from aiohttp import web

from pymodbus.datastore import ModbusServerContext, ModbusSimulatorContext
from pymodbus.datastore.simulator import Label
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.factory import ServerDecoder
from pymodbus.logging import Log
from pymodbus.pdu import ExceptionResponse
from pymodbus.server.async_io import (
    ModbusSerialServer,
    ModbusTcpServer,
    ModbusTlsServer,
    ModbusUdpServer,
)


MAX_FILTER = 1000

RESPONSE_INACTIVE = -1
RESPONSE_NORMAL = 0
RESPONSE_ERROR = 1
RESPONSE_EMPTY = 2
RESPONSE_JUNK = 3


@dataclasses.dataclass()
class CallTracer:
    """Define call/response traces."""

    call: bool = False
    fc: int = -1
    address: int = -1
    count: int = -1
    data: bytes = b""


@dataclasses.dataclass()
class CallTypeMonitor:
    """Define Request/Response monitor."""

    active: bool = False
    trace_response: bool = False
    range_start: int = -1
    range_stop: int = -1
    function: int = -1
    hex: bool = False
    decode: bool = False


@dataclasses.dataclass()
class CallTypeResponse:
    """Define Response manipulation."""

    active: int = RESPONSE_INACTIVE
    split: int = 0
    delay: int = 0
    junk_len: int = 10
    error_response: int = 0
    change_rate: int = 0
    clear_after: int = 1


class ModbusSimulatorServer:
    """**ModbusSimulatorServer**.

    :param modbus_server: Server name in json file (default: "server")
    :param modbus_device: Device name in json file (default: "client")
    :param http_host: TCP host for HTTP (default: "localhost")
    :param http_port: TCP port for HTTP (default: 8080)
    :param json_file: setup file (default: "setup.json")
    :param custom_actions_module: python module with custom actions (default: none)

    if either http_port or http_host is none, HTTP will not be started.
    This class starts a http server, that serves a couple of endpoints:

    - **"<addr>/"** static files
    - **"<addr>/api/log"** log handling, HTML with GET, REST-API with post
    - **"<addr>/api/registers"** register handling, HTML with GET, REST-API with post
    - **"<addr>/api/calls"** call (function code / message) handling, HTML with GET, REST-API with post
    - **"<addr>/api/server"** server handling, HTML with GET, REST-API with post

    Example::

        from pymodbus.server import ModbusSimulatorServer

        async def run():
            simulator = ModbusSimulatorServer(
                modbus_server="my server",
                modbus_device="my device",
                http_host="localhost",
                http_port=8080)
            await simulator.run_forever(only_start=True)
            ...
            await simulator.stop()
    """

    def __init__(
        self,
        modbus_server: str = "server",
        modbus_device: str = "device",
        http_host: str = "0.0.0.0",
        http_port: int = 8080,
        log_file: str = "server.log",
        json_file: str = "setup.json",
        custom_actions_module: str | None = None,
    ):
        """Initialize http interface."""
        if AIOHTTP_MISSING:
            raise RuntimeError(
                "Simulator server requires aiohttp. "
                'Please install with "pip install aiohttp" and try again.'
            )
        with open(json_file, encoding="utf-8") as file:
            setup = json.load(file)

        comm_class = {
            "serial": ModbusSerialServer,
            "tcp": ModbusTcpServer,
            "tls": ModbusTlsServer,
            "udp": ModbusUdpServer,
        }
        if custom_actions_module:
            actions_module = importlib.import_module(custom_actions_module)
            custom_actions_dict = actions_module.custom_actions_dict
        else:
            custom_actions_dict = {}
        server = setup["server_list"][modbus_server]
        if server["comm"] != "serial":
            server["address"] = (server["host"], server["port"])
            del server["host"]
            del server["port"]
        device = setup["device_list"][modbus_device]
        self.datastore_context = ModbusSimulatorContext(
            device, custom_actions_dict or {}
        )
        datastore = ModbusServerContext(slaves=self.datastore_context, single=True)
        comm = comm_class[server.pop("comm")]
        framer = server.pop("framer")
        if "identity" in server:
            server["identity"] = ModbusDeviceIdentification(
                info_name=server["identity"]
            )
        self.modbus_server = comm(framer=framer, context=datastore, **server)
        self.serving: asyncio.Future = asyncio.Future()
        self.log_file = log_file
        self.site: web.TCPSite | None = None
        self.runner: web.AppRunner
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
        self.generator_html: dict[str, list] = {
            "log": ["", self.build_html_log],
            "registers": ["", self.build_html_registers],
            "calls": ["", self.build_html_calls],
            "server": ["", self.build_html_server],
        }
        self.generator_json: dict[str, list] = {
            "log_json": [None, self.build_json_log],
            "registers_json": [None, self.build_json_registers],
            "calls_json": [None, self.build_json_calls],
            "server_json": [None, self.build_json_server],
        }
        self.submit = {
            "Clear": self.action_clear,
            "Stop": self.action_stop,
            "Reset": self.action_reset,
            "Add": self.action_add,
            "Monitor": self.action_monitor,
            "Set": self.action_set,
            "Simulate": self.action_simulate,
        }
        for entry in self.generator_html:  # pylint: disable=consider-using-dict-items
            html_file = os.path.join(self.web_path, "generator", entry)
            with open(html_file, encoding="utf-8") as handle:
                self.generator_html[entry][0] = handle.read()
        self.refresh_rate = 0
        self.register_filter: list[int] = []
        self.call_list: list[CallTracer] = []
        self.request_lookup = ServerDecoder.getFCdict()
        self.call_monitor = CallTypeMonitor()
        self.call_response = CallTypeResponse()
        self.api_key: web.AppKey = web.AppKey("modbus_server")

    async def start_modbus_server(self, app):
        """Start Modbus server as asyncio task."""
        try:
            if getattr(self.modbus_server, "start", None):
                await self.modbus_server.start()
            app[self.api_key] = asyncio.create_task(
                self.modbus_server.serve_forever()
            )
            app[self.api_key].set_name("simulator modbus server")
        except Exception as exc:
            Log.error("Error starting modbus server, reason: {}", exc)
            raise exc
        Log.info(
            "Modbus server started on {}", self.modbus_server.comm_params.source_address
        )

    async def stop_modbus_server(self, app):
        """Stop modbus server."""
        Log.info("Stopping modbus server")
        await self.modbus_server.shutdown()
        app[self.api_key].cancel()
        with contextlib.suppress(asyncio.exceptions.CancelledError):
            await app[self.api_key]

        Log.info("Modbus server Stopped")

    async def run_forever(self, only_start=False):
        """Start modbus and http servers."""
        try:
            self.runner = web.AppRunner(self.web_app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, self.http_host, self.http_port)
            await self.site.start()
        except Exception as exc:
            Log.error("Error starting http server, reason: {}", exc)
            raise exc
        Log.info("HTTP server started on ({}:{})", self.http_host, self.http_port)
        if only_start:
            return
        await self.serving

    async def stop(self):
        """Stop modbus and http servers."""
        await self.runner.cleanup()
        self.site = None
        if not self.serving.done():
            self.serving.set_result(True)
        await asyncio.sleep(0)

    async def handle_html_static(self, request):
        """Handle static html."""
        if not (page := request.path[1:]):
            page = "index.html"
        file = os.path.normpath(os.path.join(self.web_path, page))
        if not file.startswith(self.web_path):
            raise ValueError(f"File access outside {self.web_path} not permitted.")
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
        new_page = self.generator_html[page_type][1](params, html)
        return web.Response(text=new_page, content_type="text/html")

    async def handle_json(self, request):
        """Handle api registers."""
        page_type = request.path.split("/")[-1]
        params = await request.post()
        json_dict = self.generator_html[page_type][0].copy()
        result = self.generator_json[page_type][1](params, json_dict)
        return web.Response(text=f"json build: {page_type} - {params} - {result}")

    def build_html_registers(self, params, html):
        """Build html registers page."""
        result_txt, foot = self.helper_build_html_submit(params)
        if not result_txt:
            result_txt = "ok"
        if not foot:
            if self.register_filter:
                foot = f"{len(self.register_filter)} register(s) monitored"
            else:
                foot = "Nothing selected"
        register_types = "".join(
            f"<option value={reg_id}>{name}</option>"
            for name, reg_id in self.datastore_context.registerType_name_to_id.items()
        )
        register_actions = "".join(
            f"<option value={action_id}>{name}</option>"
            for name, action_id in self.datastore_context.action_name_to_id.items()
        )
        rows = ""
        for i in self.register_filter:
            inx, reg = self.datastore_context.get_text_register(i)
            if reg.type == Label.next:
                continue
            row = "".join(
                f"<td>{entry}</td>"
                for entry in (
                    inx,
                    reg.type,
                    reg.access,
                    reg.action,
                    reg.value,
                    reg.count_read,
                    reg.count_write,
                )
            )
            rows += f"<tr>{row}</tr>"
        new_html = (
            html.replace("<!--REGISTER_ACTIONS-->", register_actions)
            .replace("<!--REGISTER_TYPES-->", register_types)
            .replace("<!--REGISTER_FOOT-->", foot)
            .replace("<!--REGISTER_ROWS-->", rows)
            .replace("<!--RESULT-->", result_txt)
        )
        return new_html

    def build_html_calls(self, params: dict, html: str) -> str:
        """Build html calls page."""
        result_txt, foot = self.helper_build_html_submit(params)
        if not foot:
            foot = "Montitoring active" if self.call_monitor.active else "not active"
        if not result_txt:
            result_txt = "ok"

        function_error = ""
        for i, txt in (
            (1, "IllegalFunction"),
            (2, "IllegalAddress"),
            (3, "IllegalValue"),
            (4, "SlaveFailure"),
            (5, "Acknowledge"),
            (6, "SlaveBusy"),
            (7, "MemoryParityError"),
            (10, "GatewayPathUnavailable"),
            (11, "GatewayNoResponse"),
        ):
            selected = "selected" if i == self.call_response.error_response else ""
            function_error += f"<option value={i} {selected}>{txt}</option>"
        range_start_html = (
            str(self.call_monitor.range_start)
            if self.call_monitor.range_start != -1
            else ""
        )
        range_stop_html = (
            str(self.call_monitor.range_stop)
            if self.call_monitor.range_stop != -1
            else ""
        )
        function_codes = ""
        for function in self.request_lookup.values():
            selected = (
                "selected"
                if function.function_code == self.call_monitor.function  #type: ignore[attr-defined]
                else ""
            )
            function_codes += f"<option value={function.function_code} {selected}>{function.function_code_name}</option>"  #type: ignore[attr-defined]
        simulation_action = (
            "ACTIVE" if self.call_response.active != RESPONSE_INACTIVE else ""
        )

        max_len = MAX_FILTER if self.call_monitor.active else 0
        while len(self.call_list) > max_len:
            del self.call_list[0]
        call_rows = ""
        for entry in reversed(self.call_list):
            # req_obj = self.request_lookup[entry[1]]
            call_rows += f"<tr><td>{entry.call} - {entry.fc}</td><td>{entry.address}</td><td>{entry.count}</td><td>{entry.data.decode()}</td></tr>"
            # line += req_obj.funcion_code_name
        new_html = (
            html.replace("<!--SIMULATION_ACTIVE-->", simulation_action)
            .replace("FUNCTION_RANGE_START", range_start_html)
            .replace("FUNCTION_RANGE_STOP", range_stop_html)
            .replace("<!--FUNCTION_CODES-->", function_codes)
            .replace(
                "FUNCTION_SHOW_HEX_CHECKED", "checked" if self.call_monitor.hex else ""
            )
            .replace(
                "FUNCTION_SHOW_DECODED_CHECKED",
                "checked" if self.call_monitor.decode else "",
            )
            .replace(
                "FUNCTION_RESPONSE_NORMAL_CHECKED",
                "checked" if self.call_response.active == RESPONSE_NORMAL else "",
            )
            .replace(
                "FUNCTION_RESPONSE_ERROR_CHECKED",
                "checked" if self.call_response.active == RESPONSE_ERROR else "",
            )
            .replace(
                "FUNCTION_RESPONSE_EMPTY_CHECKED",
                "checked" if self.call_response.active == RESPONSE_EMPTY else "",
            )
            .replace(
                "FUNCTION_RESPONSE_JUNK_CHECKED",
                "checked" if self.call_response.active == RESPONSE_JUNK else "",
            )
            .replace(
                "FUNCTION_RESPONSE_SPLIT_CHECKED",
                "checked" if self.call_response.split > 0 else "",
            )
            .replace("FUNCTION_RESPONSE_SPLIT_DELAY", str(self.call_response.split))
            .replace(
                "FUNCTION_RESPONSE_CR_CHECKED",
                "checked" if self.call_response.change_rate > 0 else "",
            )
            .replace("FUNCTION_RESPONSE_CR_PCT", str(self.call_response.change_rate))
            .replace("FUNCTION_RESPONSE_DELAY", str(self.call_response.delay))
            .replace("FUNCTION_RESPONSE_JUNK", str(self.call_response.junk_len))
            .replace("<!--FUNCTION_ERROR-->", function_error)
            .replace(
                "FUNCTION_RESPONSE_CLEAR_AFTER", str(self.call_response.clear_after)
            )
            .replace("<!--FC_ROWS-->", call_rows)
            .replace("<!--FC_FOOT-->", foot)
        )
        return new_html

    def build_html_log(self, _params, html):
        """Build html log page."""
        return html

    def build_html_server(self, _params, html):
        """Build html server page."""
        return html

    def build_json_registers(self, params, json_dict):
        """Build html registers page."""
        return f"json build registers: {params} - {json_dict}"

    def build_json_calls(self, params, json_dict):
        """Build html calls page."""
        return f"json build calls: {params} - {json_dict}"

    def build_json_log(self, params, json_dict):
        """Build json log page."""
        return f"json build log: {params} - {json_dict}"

    def build_json_server(self, params, json_dict):
        """Build html server page."""
        return f"json build server: {params} - {json_dict}"

    def helper_build_html_submit(self, params):
        """Build html register submit."""
        try:
            range_start = int(params.get("range_start", -1))
        except ValueError:
            range_start = -1
        try:
            range_stop = int(params.get("range_stop", range_start))
        except ValueError:
            range_stop = -1
        if (submit := params["submit"]) not in self.submit:
            return None, None
        return self.submit[submit](params, range_start, range_stop)

    def action_clear(self, _params, _range_start, _range_stop):
        """Clear register filter."""
        self.register_filter = []
        return None, None

    def action_stop(self, _params, _range_start, _range_stop):
        """Stop call monitoring."""
        self.call_monitor = CallTypeMonitor()
        self.modbus_server.response_manipulator = None
        self.modbus_server.request_tracer = None
        return None, "Stopped monitoring"

    def action_reset(self, _params, _range_start, _range_stop):
        """Reset call simulation."""
        self.call_response = CallTypeResponse()
        if not self.call_monitor.active:
            self.modbus_server.response_manipulator = self.server_response_manipulator
        return None, None

    def action_add(self, params, range_start, range_stop):
        """Build list of registers matching filter."""
        reg_action = int(params.get("action", -1))
        reg_writeable = "writeable" in params
        reg_type = int(params.get("type", -1))
        filter_updated = 0
        if range_start != -1:
            steps = range(range_start, range_stop + 1)
        else:
            steps = range(1, self.datastore_context.register_count)
        for i in steps:
            if range_start != -1 and (i < range_start or i > range_stop):
                continue
            reg = self.datastore_context.registers[i]
            skip_filter = reg_writeable and not reg.access
            skip_filter |= reg_type not in (-1, reg.type)
            skip_filter |= reg_action not in (-1, reg.action)
            skip_filter |= i in self.register_filter
            if skip_filter:
                continue
            self.register_filter.append(i)
            filter_updated += 1
            if len(self.register_filter) >= MAX_FILTER:
                self.register_filter.sort()
                return None, f"Max. filter size {MAX_FILTER} exceeded!"
        self.register_filter.sort()
        return None, None

    def action_monitor(self, params, range_start, range_stop):
        """Start monitoring calls."""
        self.call_monitor.range_start = range_start
        self.call_monitor.range_stop = range_stop
        self.call_monitor.function = (
            int(params["function"]) if params["function"] else -1
        )
        self.call_monitor.hex = "show_hex" in params
        self.call_monitor.decode = "show_decode" in params
        self.call_monitor.active = True
        self.modbus_server.response_manipulator = self.server_response_manipulator
        self.modbus_server.request_tracer = self.server_request_tracer
        return None, None

    def action_set(self, params, _range_start, _range_stop):
        """Set register value."""
        if not (register := params["register"]):
            return "Missing register", None
        register = int(register)
        if value := params["value"]:
            self.datastore_context.registers[register].value = int(value)
        if bool(params.get("writeable", False)):
            self.datastore_context.registers[register].access = True
        return None, None

    def action_simulate(self, params, _range_start, _range_stop):
        """Simulate responses."""
        self.call_response.active = int(params["response_type"])
        if "response_split" in params:
            if params["split_delay"]:
                self.call_response.split = int(params["split_delay"])
            else:
                self.call_response.split = 1
        else:
            self.call_response.split = 0
        if "response_cr" in params:
            if params["response_cr_pct"]:
                self.call_response.change_rate = int(params["response_cr_pct"])
            else:
                self.call_response.change_rate = 0
        else:
            self.call_response.change_rate = 0
        if params["response_delay"]:
            self.call_response.delay = int(params["response_delay"])
        else:
            self.call_response.delay = 0
        if params["response_junk_datalen"]:
            self.call_response.junk_len = int(params["response_junk_datalen"])
        else:
            self.call_response.junk_len = 0
        self.call_response.error_response = int(params["response_error"])
        if params["response_clear_after"]:
            self.call_response.clear_after = int(params["response_clear_after"])
        else:
            self.call_response.clear_after = 1
        self.modbus_server.response_manipulator = self.server_response_manipulator
        return None, None

    def server_response_manipulator(self, response):
        """Manipulate responses.

        All server responses passes this filter before being sent.
        The filter returns:

        - response, either original or modified
        - skip_encoding, signals whether or not to encode the response
        """
        if self.call_monitor.trace_response:
            tracer = CallTracer(
                call=False,
                fc=response.function_code,
                address=response.address if hasattr(response, "address") else -1,
                count=response.count if hasattr(response, "count") else -1,
                data=b"-",
            )
            self.call_list.append(tracer)
            self.call_monitor.trace_response = False

        if self.call_response.active != RESPONSE_INACTIVE:
            return response, False

        skip_encoding = False
        if self.call_response.active == RESPONSE_EMPTY:
            Log.warning("Sending empty response")
            response.should_respond = False
        elif self.call_response.active == RESPONSE_NORMAL:
            if self.call_response.delay:
                Log.warning(
                    "Delaying response by {}s for all incoming requests",
                    self.call_response.delay,
                )
                sleep(self.call_response.delay)  # change to async
            else:
                pass
                # self.call_response.change_rate
                # self.call_response.split
        elif self.call_response.active == RESPONSE_ERROR:
            Log.warning("Sending error response for all incoming requests")
            err_response = ExceptionResponse(
                response.function_code, self.call_response.error_response
            )
            err_response.transaction_id = response.transaction_id
            err_response.slave_id = response.slave_id
        elif self.call_response.active == RESPONSE_JUNK:
            response = os.urandom(self.call_response.junk_len)
            skip_encoding = True

        self.call_response.clear_after -= 1
        if self.call_response.clear_after <= 0:
            Log.info("Resetting manipulator due to clear_after")
            self.call_response.active = RESPONSE_EMPTY
        return response, skip_encoding

    def server_request_tracer(self, request, *_addr):
        """Trace requests.

        All server requests passes this filter before being handled.
        """
        if self.call_monitor.function not in {-1, request.function_code}:
            return
        address = request.address if hasattr(request, "address") else -1
        if self.call_monitor.range_start != -1 and address != -1:
            if (
                self.call_monitor.range_start > address
                or self.call_monitor.range_stop < address
            ):
                return
        tracer = CallTracer(
            call=True,
            fc=request.function_code,
            address=address,
            count=request.count if hasattr(request, "count") else -1,
            data=b"-",
        )
        self.call_list.append(tracer)
        self.call_monitor.trace_response = True

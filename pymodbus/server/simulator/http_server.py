"""HTTP server for modbus simulator."""
import asyncio
import dataclasses
import importlib
import json
import logging
import os


try:
    from aiohttp import web
except ImportError:
    web = None

from pymodbus.datastore import ModbusServerContext, ModbusSimulatorContext
from pymodbus.datastore.simulator import Label
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

RESPONSE_NORMAL = 0
RESPONSE_ERROR = 1
RESPONSE_EMPTY = 2
RESPONSE_JUNK = 3


@dataclasses.dataclass()
class CallTypeMonitor:
    """Define Request/Response monitor"""

    active: bool = False
    range_start: int = ""
    range_stop: int = ""
    function: int = -1
    hex: bool = False
    decode: bool = False


@dataclasses.dataclass()
class CallTypeResponse:
    """Define Response manipulation"""

    active: int = RESPONSE_NORMAL
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
    :param http_host: TCP host for HTTP (default: 8080)
    :param http_port: TCP port for HTTP (default: "localhost")
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
        self.generator_json = {
            "log_json": [None, self.build_json_log],
            "registers_json": [None, self.build_json_registers],
            "calls_json": [None, self.build_json_calls],
            "server_json": [None, self.build_json_server],
        }
        for entry in self.generator_html:  # pylint: disable=consider-using-dict-items
            file = os.path.join(self.web_path, "generator", entry)
            with open(file, encoding="utf-8") as handle:
                self.generator_html[entry][0] = handle.read()
        self.refresh_rate = 0
        self.register_filter = []
        self.call_monitor = CallTypeMonitor()
        self.call_response = CallTypeResponse()

    async def start_modbus_server(self, app):
        """Start Modbus server as asyncio task."""
        self.modbus_server.response_manipulator = self.server_response_manipulator
        self.modbus_server.request_tracer = self.server_request_tracer
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
        page_type = request.path.split("/")[-1]
        params = await request.post()
        json_dict = self.generator_html[page_type][0].copy()
        result = await self.generator_json[page_type][1](params, json_dict)
        return web.Response(text=f"json build: {page_type} - {params} - {result}")

    def helper_build_html_registers_submit(self, params):
        """Build html register submit."""
        result_txt = "ok"
        register_foot = ""
        if params["submit"] == "Add":
            res_ok, txt = self.helper_build_filter(params)
            if not res_ok:
                result_txt = txt
            else:
                register_foot = txt
        elif params["submit"] == "Clear":
            self.register_filter = []
        elif params["submit"] == "Set":
            if not (register := params["register"]):
                result_txt = "Missing register"
            else:
                register = int(register)
                if value := params["value"]:
                    self.datastore_context.registers[register].value = int(value)
                if bool(params.get("writeable", False)):
                    self.datastore_context.registers[
                        register
                    ].access = not self.datastore_context.registers[register].access
        return result_txt, register_foot

    async def build_html_registers(self, params, html):
        """Build html registers page."""
        result_txt, register_foot = self.helper_build_html_registers_submit(params)
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
            .replace("<!--REGISTER_FOOT-->", register_foot)
            .replace("<!--REGISTER_ROWS-->", rows)
            .replace("<!--RESULT-->", result_txt)
        )
        return new_html

    async def build_html_log(self, _params, html):
        """Build html log page."""
        return html

    def helper_build_html_calls_submit_monitor(self, params):
        """Build html calls submit."""
        if params["range_start"]:
            self.call_monitor.range_start = int(params["range_start"])
            if params["range_stop"]:
                self.call_monitor.range_stop = int(params["range_stop"])
            else:
                self.call_monitor.range_stop = self.call_monitor.range_start
        else:
            self.call_monitor.range_start = ""
            self.call_monitor.range_stop = ""
        if params["function"]:
            self.call_monitor.function = int(params["function"])
        else:
            self.call_monitor.function = ""
        self.call_monitor.hex = "show_hex" in params
        self.call_monitor.decode = "show_decode" in params
        self.call_monitor.active = True

    def helper_build_html_calls_submit_set(self, params):
        """Build html calls submit."""
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

    def helper_build_html_calls_submit(self, params):
        """Build html calls submit."""
        call_foot = ""
        if params["submit"] == "Clear":
            call_foot = f"clear --{params}--"
            # JAN Clear trace list.
        elif params["submit"] == "Stop":
            self.call_monitor = CallTypeMonitor()
            # JAN Clear trace list
        elif params["submit"] == "Reset":
            self.call_response = CallTypeResponse()
        return call_foot

    async def build_html_calls(self, params, html):
        """Build html calls page."""
        call_foot = ""
        if params["submit"] == "Monitor":
            self.helper_build_html_calls_submit_monitor(params)
        elif params["submit"] == "Set":
            self.helper_build_html_calls_submit_set(params)
        else:
            call_foot = self.helper_build_html_calls_submit(params)
        function_error = ""
        for i, txt in (
            (-1, "Any"),
            (0, "None"),
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
        html = (
            html.replace("FUNCTION_RANGE_START", str(self.call_monitor.range_start))
            .replace("FUNCTION_RANGE_STOP", str(self.call_monitor.range_stop))
            .replace("<!--FUNCTION_TYPES-->", function_error)
            .replace(
                "FUNCTION_SHOW_HEX_CHECKED", "checked" if self.call_monitor.hex else ""
            )
            .replace(
                "FUNCTION_SHOW_DECODED_CHECKED",
                "checked" if self.call_monitor.decode else "",
            )
            .replace(
                "<!--FUNCTION_MONITORING_ACTIVE-->",
                '"MONITORING"' if self.call_monitor.active else "",
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
        )

        # <!--FC_ROWS-->
        # <!--FC_FOOT-->
        #

        new_html = html.replace("<!--FC_FOOT-->", call_foot)
        return new_html

    async def build_html_server(self, _params, html):
        """Build html server page."""
        return html

    async def build_json_log(self, params, json_dict):
        """Build json log page."""
        return f"json build log: {params} - {json_dict}"

    async def build_json_registers(self, params, json_dict):
        """Build html registers page."""
        return f"json build registers: {params} - {json_dict}"

    async def build_json_calls(self, params, json_dict):
        """Build html calls page."""
        return f"json build calls: {params} - {json_dict}"

    async def build_json_server(self, params, json_dict):
        """Build html server page."""
        return f"json build server: {params} - {json_dict}"

    def helper_build_filter(self, params):
        """Build list of registers matching filter."""
        if x := params.get("range_start"):
            range_start = int(x)
        else:
            range_start = -1
        if x := params.get("range_stop"):
            range_stop = int(x)
        else:
            range_stop = range_start
        reg_action = int(params["action"])
        reg_writeable = "writeable" in params
        reg_type = int(params["type"])
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
                return True, f"Max. filter size {MAX_FILTER} exceeded!"
        self.register_filter.sort()
        return True, (
            f"Added {filter_updated} registers."
            if filter_updated
            else "NO registers added."
        )

    def server_response_manipulator(self, response):
        """Manipulate responses.

        All server responses passes this filter before being sent.
        The filter returns:

        - response, either original or modified
        - skip_encoding, signals whether or not to encode the response
        """
        return response, False

        # ---------------------
        # ORIGINAL
        # skip_encoding = False
        # if not self._manipulator_config:
        #     return response
        #
        # clear_after = self._manipulator_config.get("clear_after")
        # if clear_after and self._counter > clear_after:
        #     txt = f"Resetting manipulator after {clear_after} responses"
        #     logger.info(txt)
        #     self.update_manipulator_config(dict(DEFAULT_MANIPULATOR))
        #     return response
        # response_type = self._manipulator_config.get("response_type")
        # if response_type == "error":
        #     error_code = self._manipulator_config.get("error_code")
        #     logger.warning("Sending error response for all incoming requests")
        #     err_response = ExceptionResponse(response.function_code, error_code)
        #     err_response.transaction_id = response.transaction_id
        #     err_response.unit_id = response.unit_id
        #     response = err_response
        #     self._counter += 1
        # elif response_type == "delayed":
        #     delay_by = self._manipulator_config.get("delay_by")
        #     txt = f"Delaying response by {delay_by}s for all incoming requests"
        #     logger.warning(txt)
        #     time.sleep(delay_by)  # change to async
        #     self._counter += 1
        # elif response_type == "empty":
        #     logger.warning("Sending empty response")
        #     self._counter += 1
        #     response.should_respond = False
        # elif response_type == "stray":
        #     if (data_len := self._manipulator_config.get("data_len", 10)) <= 0:
        #         txt = f"Invalid data_len {data_len}, using default 10"
        #         logger.warning(txt)
        #         data_len = 10
        #     response = os.urandom(data_len)
        #     self._counter += 1
        #     skip_encoding = True
        # return response, skip_encoding

    def server_request_tracer(self, request, *addr):
        """Trace requests.

        All server requests passes this filter before being handled.
        """

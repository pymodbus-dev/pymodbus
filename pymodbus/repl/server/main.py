"""Repl server main.

Copyright (c) 2020 by RiptideIO
All rights reserved.
"""
import sys
import logging
import asyncio
import json
import click
from pymodbus.framer.socket_framer import ModbusSocketFramer
from pymodbus.server.reactive.main import (
    ReactiveServer,
    DEFAULT_FRAMER,
    DEFUALT_HANDLERS,
)
from pymodbus.server.reactive.default_config import DEFUALT_CONFIG
from pymodbus.repl.server.cli import run_repl

if sys.version_info > (3, 7):
    CANCELLED_ERROR = asyncio.exceptions.CancelledError
else:
    CANCELLED_ERROR = asyncio.CancelledError  # pylint: disable=invalid-name

_logger = logging.getLogger(__name__)


CONTEXT_SETTING = {"allow_extra_args": True, "ignore_unknown_options": True}

class ModbusServerConfig:


@click.group("ReactiveModbusServer")
@click.option("-h", "--host", default="localhost", help="Host address",
              show_default=True)
@click.option("-p", "--web-port", default=8080, help="Web app port",
              show_default=True)
@click.option("-b", "--broadcast-support", is_flag=True,
              default=False, help="Support broadcast messages",
              show_default=True)
@click.option("--repl/--no-repl", is_flag=True,
              default=True, help="Enable/Disable repl for server",
              show_default=True)
@click.option("--verbose", is_flag=True,
              help="Run with debug logs enabled for pymodbus",
              show_default=True)
@click.pass_context
def server(ctx, host, web_port, broadcast_support, repl, verbose):
    """Server code."""
    FORMAT = ('%(asctime)-15s %(threadName)-15s'
              ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
    pymodbus_logger = logging.getLogger("pymodbus")
    logging.basicConfig(format=FORMAT)
    logger = logging.getLogger(__name__)
    if verbose:
        pymodbus_logger.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    else:
        pymodbus_logger.setLevel(logging.ERROR)
        logger.setLevel(logging.ERROR)

    ctx.obj = {
        "repl": repl,
        "host": host,
        "web_port": web_port,
        "broadcast": broadcast_support,
    }


@server.command("run", context_settings=CONTEXT_SETTING)
@click.option("-s", "--modbus-server", default="tcp",
              type=click.Choice(["tcp", "serial", "tls", "udp"],
                                case_sensitive=False),
              show_default=True,
              help="Modbus server")
@click.option("-f", "--modbus-framer", default="socket",
              type=click.Choice(["socket", "rtu", "tls", "ascii", "binary"],
                                case_sensitive=False),
              show_default=True,
              help="Modbus framer to use")
@click.option("-mp", "--modbus-port", default="5020", help="Modbus port")
@click.option("-u", "--modbus-unit-id", default=[1], type=int,
              multiple=True, help="Modbus unit id")
@click.option("--modbus-config", type=click.Path(exists=True),
              help="Path to additional modbus server config")
@click.option("-r", "--randomize", default=0, help="Randomize every `r` reads."
                                                   " 0=never, 1=always, "
                                                   "2=every-second-read, "
                                                   "and so on. "
                                                   "Applicable IR and DI.",
              show_default=True)
@click.pass_context
def run(ctx, modbus_server, modbus_framer, modbus_port, modbus_unit_id,
        modbus_config, randomize):
    """
    Run Reactive Modbus server exposing REST endpoint
    for response manipulation.
    """
    repl = ctx.obj.pop("repl")
    extra_args = ctx.args
    web_app_config = ctx.obj
    loop = asyncio.get_event_loop()
    framer = DEFAULT_FRAMER.get(modbus_framer, ModbusSocketFramer)
    if modbus_config:
        with open(modbus_config) as my_file:  # pylint: disable=unspecified-encoding
            modbus_config = json.load(my_file)
    else:
        modbus_config = DEFUALT_CONFIG

    modbus_config = modbus_config.get(modbus_server, {})

    if modbus_server != "serial":
        modbus_port = int(modbus_port)
        handler = modbus_config.pop("handler", "ModbusConnectedRequestHandler")
    else:
        handler = modbus_config.pop("handler", "ModbusSingleRequestHandler")
    handler = DEFUALT_HANDLERS.get(handler.strip())

    modbus_config["handler"] = handler
    modbus_config["randomize"] = randomize
    app = ReactiveServer.factory(
        modbus_server,
        framer,
        modbus_port=modbus_port,
        unit=modbus_unit_id,
        loop=loop,
        **web_app_config,
        **modbus_config
    )
    try:
        if repl:
            loop.run_until_complete(app.run_async())

            loop.run_until_complete(run_repl(app))
            loop.run_forever()
        else:
            app.run()

    except CANCELLED_ERROR:
        print("Done!!!!!")


if __name__ == "__main__":
    server()  # pylint: disable=no-value-for-parameter

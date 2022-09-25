"""Repl server main."""
from __future__ import annotations

import asyncio
from enum import Enum
import json
import logging
from pathlib import Path
from typing import List

import typer

from pymodbus.framer.socket_framer import ModbusSocketFramer
from pymodbus.repl.server.cli import run_repl
from pymodbus.server.reactive.default_config import DEFUALT_CONFIG
from pymodbus.server.reactive.main import (
    DEFAULT_FRAMER,
    DEFUALT_HANDLERS,
    ReactiveServer,
)


CANCELLED_ERROR = asyncio.exceptions.CancelledError

_logger = logging.getLogger(__name__)

CONTEXT_SETTING = {"allow_extra_args": True, "ignore_unknown_options": True}

# TBD class ModbusServerConfig:


class ModbusServerTypes(str, Enum):
    """Server types."""

    # ["tcp", "serial", "tls", "udp"]
    tcp = "tcp"  # pylint: disable=invalid-name
    serial = "serial"  # pylint: disable=invalid-name
    tls = "tls"  # pylint: disable=invalid-name
    udp = "udp"  # pylint: disable=invalid-name


class ModbusFramerTypes(str, Enum):
    """Framer types."""

    # ["socket", "rtu", "tls", "ascii", "binary"]
    socket = "socket"  # pylint: disable=invalid-name
    rtu = "rtu"  # pylint: disable=invalid-name
    tls = "tls"  # pylint: disable=invalid-name
    ascii = "ascii"  # pylint: disable=invalid-name
    binary = "binary"  # pylint: disable=invalid-name


def _completer(incomplete: str, valid_values: List[str]) -> List[str]:
    """Complete value."""
    completion = []
    for name in valid_values:
        if name.startswith(incomplete):
            completion.append(name)
    return completion


def framers(incomplete: str) -> List[str]:
    """Return an autocompleted list of supported clouds."""
    _framers = ["socket", "rtu", "tls", "ascii", "binary"]
    return _completer(incomplete, _framers)


def servers(incomplete: str) -> List[str]:
    """Return an autocompleted list of supported clouds."""
    _servers = ["tcp", "serial", "tls", "udp"]
    return _completer(incomplete, _servers)


app = typer.Typer(
    no_args_is_help=True,
    context_settings=CONTEXT_SETTING,
    help="Reactive modebus server",
)


@app.callback()
def server(
    ctx: typer.Context,
    host: str = typer.Option("localhost", "--host", help="Host address"),
    web_port: int = typer.Option(8080, "--web-port", help="Web app port"),
    broadcast_support: bool = typer.Option(
        False, "-b", help="Support broadcast messages"
    ),
    repl: bool = typer.Option(True, help="Enable/Disable repl for server"),
    verbose: bool = typer.Option(
        False, help="Run with debug logs enabled for pymodbus"
    ),
):
    """Run server code."""
    FORMAT = (  # pylint: disable=invalid-name
        "%(asctime)-15s %(threadName)-15s"
        " %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
    )
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


@app.command("run", context_settings=CONTEXT_SETTING)
def run(
    ctx: typer.Context,
    modbus_server: str = typer.Option(
        ModbusServerTypes.tcp,
        "--modbus-server",
        "-s",
        case_sensitive=False,
        autocompletion=servers,
        help="Modbus Server",
    ),
    modbus_framer: str = typer.Option(
        ModbusFramerTypes.socket,
        "--framer",
        "-f",
        case_sensitive=False,
        autocompletion=framers,
        help="Modbus framer to use",
    ),
    modbus_port: str = typer.Option("5020", "--modbus-port", "-p", help="Modbus port"),
    modbus_unit_id: List[int] = typer.Option(
        None, "--unit-id", "-u", help="Supported Modbus unit id's"
    ),
    modbus_config: Path = typer.Option(
        None, help="Path to additional modbus server config"
    ),
    randomize: int = typer.Option(
        0,
        "--random",
        "-r",
        help="Randomize every `r` reads. 0=never, 1=always,2=every-second-read"
        ", and so on. Applicable IR and DI.",
    ),
):
    """Run Reactive Modbus server.

    Exposing REST endpoint for response manipulation.
    """
    repl = ctx.obj.pop("repl")
    # TBD extra_args = ctx.args
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
        single=False,
        **web_app_config,
        **modbus_config,
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
    app()
